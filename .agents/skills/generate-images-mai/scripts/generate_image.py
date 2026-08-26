#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Generate an image with Microsoft MAI-Image-2.5 via the Azure AI image generations API.

Requires AZURE_API_KEY and AZURE_IMAGE_ENDPOINT (or pass --endpoint).
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an image with Microsoft MAI-Image-2.5."
    )
    parser.add_argument("--prompt", required=True, help="Text description of the image")
    parser.add_argument("--output", type=Path, default=Path("generated_image.png"))
    parser.add_argument("--width", type=positive_int, default=1024)
    parser.add_argument("--height", type=positive_int, default=1024)
    parser.add_argument("--model", default="MAI-Image-2.5")
    parser.add_argument("--endpoint", help="Azure image generations endpoint")
    parser.add_argument("--env-file", type=Path, help="Path to a specific .env file")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file")
    return parser.parse_args()


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


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


def main() -> int:
    args = parse_args()
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

    endpoint = args.endpoint or os.environ.get("AZURE_IMAGE_ENDPOINT")
    if not endpoint:
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

    request_body = json.dumps(
        {
            "prompt": args.prompt,
            "width": args.width,
            "height": args.height,
            "model": args.model,
        }
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=request_body,
        headers={"Content-Type": "application/json", "api-key": api_key},
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

    print(f"Generated image: {output}")
    print(f"Requested dimensions: {args.width}x{args.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())