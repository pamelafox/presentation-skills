import base64
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("generate_image.py")
SPEC = importlib.util.spec_from_file_location("generate_image", SCRIPT_PATH)
assert SPEC and SPEC.loader
generate_image = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_image)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class GenerateImageTests(unittest.TestCase):
    def api_response(self) -> FakeResponse:
        image = base64.b64encode(b"result-image").decode()
        return FakeResponse(json.dumps({"data": [{"b64_json": image}]}).encode())

    def test_generation_uses_json_generations_endpoint(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return self.api_response()

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "generated.png"
            environment = {
                "AZURE_API_KEY": "test-key",
                "AZURE_IMAGE_ENDPOINT": "https://example.services.ai.azure.com/mai/v1/images/edits",
            }
            with patch.dict(os.environ, environment, clear=True), patch.object(
                generate_image, "urlopen", fake_urlopen
            ):
                result = generate_image.main(["--prompt", "A garden", "--output", str(output)])

            self.assertEqual(result, 0)
            self.assertEqual(
                captured["request"].full_url,
                "https://example.services.ai.azure.com/mai/v1/images/generations",
            )
            self.assertEqual(captured["request"].get_header("Content-type"), "application/json")
            self.assertEqual(json.loads(captured["request"].data)["prompt"], "A garden")
            self.assertEqual(output.read_bytes(), b"result-image")

    def test_edit_uses_multipart_edits_endpoint(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            return self.api_response()

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            input_image = directory / "garden.png"
            input_image.write_bytes(b"\x89PNG\r\n\x1a\nsource-image")
            output = directory / "edited.png"
            environment = {
                "AZURE_API_KEY": "test-key",
                "AZURE_IMAGE_ENDPOINT": "https://example.services.ai.azure.com/mai/v1/images/generations",
            }
            with patch.dict(os.environ, environment, clear=True), patch.object(
                generate_image, "urlopen", fake_urlopen
            ):
                result = generate_image.main(
                    [
                        "--prompt",
                        "Add native flowers",
                        "--input-image",
                        str(input_image),
                        "--output",
                        str(output),
                    ]
                )

            request = captured["request"]
            self.assertEqual(result, 0)
            self.assertEqual(
                request.full_url,
                "https://example.services.ai.azure.com/mai/v1/images/edits",
            )
            self.assertTrue(request.get_header("Content-type").startswith("multipart/form-data; boundary="))
            self.assertIn(b'name="prompt"', request.data)
            self.assertIn(b"Add native flowers", request.data)
            self.assertIn(b'name="model"', request.data)
            self.assertIn(b'name="image"; filename="garden.png"', request.data)
            self.assertIn(b"Content-Type: image/png", request.data)
            self.assertIn(b"source-image", request.data)
            self.assertEqual(output.read_bytes(), b"result-image")

    def test_edit_rejects_unsupported_input_before_request(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            input_image = directory / "garden.gif"
            input_image.write_bytes(b"GIF89a")
            output = directory / "edited.png"
            environment = {
                "AZURE_API_KEY": "test-key",
                "AZURE_IMAGE_ENDPOINT": "https://example.services.ai.azure.com/mai/v1/images/generations",
            }
            with patch.dict(os.environ, environment, clear=True), patch.object(
                generate_image, "urlopen"
            ) as mocked_urlopen:
                result = generate_image.main(
                    [
                        "--prompt",
                        "Add flowers",
                        "--input-image",
                        str(input_image),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 2)
            mocked_urlopen.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
