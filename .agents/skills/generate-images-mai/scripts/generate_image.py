#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Generate or edit an image with Microsoft MAI-Image-2.5.

Requires AZURE_API_KEY and AZURE_IMAGE_ENDPOINT (or pass --endpoint).
"""

import argparse
import base64
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or edit an image with Microsoft MAI-Image-2.5."
    )
    parser.add_argument("--prompt", required=True, help="Image description or edit instruction")
    parser.add_argument(
        "--input-image",
        type=Path,
        help="JPEG or PNG image to edit; omit for text-to-image generation",
    )
    parser.add_argument("--output", type=Path, default=Path("generated_image.png"))
    parser.add_argument("--width", type=positive_int, default=1024)
    parser.add_argument("--height", type=positive_int, default=1024)
    parser.add_argument("--model", default="MAI-Image-2.5")
    parser.add_argument("--endpoint", help="Azure resource or MAI image API endpoint")
    parser.add_argument("--env-file", type=Path, help="Path to a specific .env file")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file")
    return parser.parse_args(argv)


def find_env_file(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_env_file(path: Path) -> None:
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid .env entry at {path}:{line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def operation_endpoint(configured_endpoint: str, editing: bool) -> str:
    endpoint = configured_endpoint.rstrip("/")
    operation = "edits" if editing else "generations"
    for suffix in ("/generations", "/edits"):
        if endpoint.endswith(suffix):
            return f"{endpoint.removesuffix(suffix)}/{operation}"
    if endpoint.endswith("/mai/v1/images"):
        return f"{endpoint}/{operation}"
    if endpoint.endswith(".azure.com"):
        return f"{endpoint}/mai/v1/images/{operation}"
    return endpoint


def image_media_type(path: Path, image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    raise ValueError(f"Input image must be a JPEG or PNG: {path}")


def multipart_body(
    prompt: str,
    model: str,
    image_path: Path,
    image_bytes: bytes,
    media_type: str,
) -> tuple[bytes, str]:
    boundary = f"----mai-image-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in (("prompt", prompt), ("model", model)):
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            )
        )

    filename = image_path.name.replace('"', "")
    chunks.extend(
        (
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {media_type}\r\n\r\n".encode(),
            image_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        )
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def sanitized_api_error(error: HTTPError) -> str:
    body = error.read().decode("utf-8", errors="replace")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body[:500].strip() or error.reason

    if isinstance(payload, dict):
        detail = payload.get("error", payload)
        if isinstance(detail, dict):
            return str(detail.get("message") or detail.get("code") or "Request failed")
        return str(detail)
    return "Request failed"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env_file = args.env_file or find_env_file(Path.cwd())
    if env_file:
        try:
            load_env_file(env_file.expanduser().resolve())
        except (OSError, ValueError) as error:
            print(f"Configuration error: {error}", file=sys.stderr)
            return 2

    api_key = os.environ.get("AZURE_API_KEY")
    if not api_key:
        print("Missing AZURE_API_KEY. Add it to your environment or .env file.", file=sys.stderr)
        return 2

    configured_endpoint = args.endpoint or os.environ.get("AZURE_IMAGE_ENDPOINT")
    if not configured_endpoint:
        print(
            "Missing AZURE_IMAGE_ENDPOINT. Add it to your environment or .env file, "
            "or pass --endpoint.",
            file=sys.stderr,
        )
        return 2

    output = args.output.expanduser().resolve()
    if output.exists() and not args.force:
        print(f"Output already exists: {output}. Use --force to replace it.", file=sys.stderr)
        return 2

    editing = args.input_image is not None
    endpoint = operation_endpoint(configured_endpoint, editing)

    if editing:
        input_image = args.input_image.expanduser().resolve()
        try:
            input_bytes = input_image.read_bytes()
            media_type = image_media_type(input_image, input_bytes)
        except (OSError, ValueError) as error:
            print(f"Invalid input image: {error}", file=sys.stderr)
            return 2
        request_body, content_type = multipart_body(
            args.prompt, args.model, input_image, input_bytes, media_type
        )
    else:
        if args.width < 768 or args.height < 768:
            print("Generation width and height must each be at least 768.", file=sys.stderr)
            return 2
        if args.width * args.height > 1_048_576:
            print("Generation width x height must not exceed 1,048,576 pixels.", file=sys.stderr)
            return 2
        request_body = json.dumps(
            {
                "prompt": args.prompt,
                "width": args.width,
                "height": args.height,
                "model": args.model,
            }
        ).encode("utf-8")
        content_type = "application/json"

    request = Request(
        endpoint,
        data=request_body,
        headers={"Content-Type": content_type, "api-key": api_key},
        method="POST",
    )

    try:
        with urlopen(request, timeout=180) as response:
            payload = json.load(response)
    except HTTPError as error:
        print(
            f"Image API returned HTTP {error.code}: {sanitized_api_error(error)}",
            file=sys.stderr,
        )
        return 1
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Image request failed: {error}", file=sys.stderr)
        return 1

    try:
        encoded_image = payload["data"][0]["b64_json"]
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        print(f"Image API response did not contain valid b64_json: {error}", file=sys.stderr)
        return 1

    if not image_bytes:
        print("Image API returned an empty image.", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.name}.tmp")
    try:
        temporary_output.write_bytes(image_bytes)
        temporary_output.replace(output)
    except OSError as error:
        temporary_output.unlink(missing_ok=True)
        print(f"Could not write output image: {error}", file=sys.stderr)
        return 1

    action = "Edited" if editing else "Generated"
    print(f"{action} image: {output}")
    if not editing:
        print(f"Requested dimensions: {args.width}x{args.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
