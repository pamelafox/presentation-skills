---
name: generate-images-mai
description: 'Generate or edit bitmap images with Microsoft MAI-Image-2.5 through the Azure AI image APIs. Use for text-to-image generation, image-to-image edits, object removal or replacement, inpainting, text updates, artifact cleanup, reference-image transformations, posters, thumbnails, and concept art.'
argument-hint: 'Describe the image or edit and optionally provide an input image, output path, width, and height'
user-invocable: true
disable-model-invocation: false
---

# Generate and edit images with MAI-Image-2.5

Create an image from text or edit a supplied JPEG or PNG, save the result, and verify that the output is usable.

## Requirements

- Python 3.10+.
- A `.env` file in the current directory or one of its parents:

```dotenv
AZURE_API_KEY=your-key
AZURE_IMAGE_ENDPOINT=https://your-resource.services.ai.azure.com/mai/v1/images/generations
```

The endpoint can be the resource root, `/mai/v1/images`, `/generations`, or `/edits`; the script selects the operation-specific path.

Never read, print, return, commit, or embed the API key in generated files, commands, logs, or chat. Do not create a `.env` containing a real secret. If configuration is missing, tell the user which variable to add without asking them to send its value through chat.

## Procedure

1. Determine the requested subject or edit, intended use, output path, dimensions, and visual constraints from the conversation.
2. For an edit, confirm that the input is a readable JPEG or PNG. Preserve the original composition or identity unless the request says otherwise.
3. If the prompt is underspecified, preserve the user's intent and add only useful visual detail: medium, composition, environment, lighting, palette, camera or rendering style, and important exclusions. Do not introduce brands, people, text, or sensitive attributes the user did not request.
4. Default to `1024x1024` and `generated_image.png` for generation. Generation dimensions must each be at least 768 pixels and contain no more than 1,048,576 total pixels. Edit output is always PNG and dimensions are controlled by the service.
5. Run [generate_image.py](./scripts/generate_image.py) with the refined prompt. Pass arguments as separate shell tokens and quote all user-provided values.

Text-to-image generation:

```bash
python3 .agents/skills/generate-images-mai/scripts/generate_image.py \
  --prompt "A photograph of a red fox in an autumn forest" \
  --width 1024 \
  --height 1024 \
  --output generated_image.png
```

Image-to-image edit:

```bash
python3 .agents/skills/generate-images-mai/scripts/generate_image.py \
  --prompt "Replace the lawn with a native wildflower garden while preserving the house and paths" \
  --input-image garden.png \
  --output edited_garden.png
```

6. If the destination exists, do not overwrite it unless the user explicitly requested replacement; use a new descriptive filename or pass `--force` only with that permission.
7. Verify the output exists, is non-empty, and can be decoded as an image. Use the image-viewing tool to inspect it when available.
8. Check that the result matches the requested subject or edit, composition, legibility, and safety constraints. Regenerate with a targeted prompt adjustment when the image is blank, malformed, materially off-topic, or has obvious layout defects.
9. Report the saved path and, when available, final dimensions. Mention prompt changes only when they materially affect the user's request.

## Options

- `--prompt`: Required image description or editing instruction.
- `--input-image`: Optional JPEG or PNG image to edit. When present, the script uses the MAI image edits API.
- `--output`: Output PNG path; defaults to `generated_image.png`.
- `--width` and `--height`: Generation dimensions; each defaults to `1024`. Ignored for edits.
- `--model`: Deployment name; defaults to `MAI-Image-2.5`.
- `--endpoint`: Azure resource or image API endpoint; overrides `AZURE_IMAGE_ENDPOINT`.
- `--env-file`: Loads a specific `.env` file instead of searching parent directories.
- `--force`: Permits replacing an existing output file.

Environment variables already present in the process take precedence over values in `.env`.

## API behavior

- Text generation sends JSON to `/mai/v1/images/generations`.
- Image editing sends `prompt`, `model`, and one `image` as multipart form data to `/mai/v1/images/edits`.
- Image edits accept JPEG or PNG input and return PNG output.
- MAI-Image-2.5 image editing is currently a public-preview feature and isn't recommended for production workloads without accounting for preview limitations.

## Failure handling

- Missing configuration: Identify `AZURE_API_KEY` or `AZURE_IMAGE_ENDPOINT` and stop.
- Invalid input image: Report that image edits require a readable JPEG or PNG.
- HTTP authentication failure: Tell the user to verify `AZURE_API_KEY` locally; never request the key in chat.
- HTTP endpoint or deployment failure: Report the status and sanitized API message, then verify the endpoint and deployment name.
- Invalid or absent `b64_json`: Do not create an output file; report the response-shape problem.
- Content-policy rejection: Explain that the service rejected the prompt and offer a compliant revision.
- Corrupt or empty image: Remove the incomplete output and retry once with the same request before changing the prompt.

## Completion checks

- The secret was not exposed.
- The requested output was created without overwriting unrelated work.
- The file is a decodable image.
- Visual inspection confirms the primary subject and requested edits are present.
- The user receives a clickable path to the image.

## Reference

- [Deploy and use MAI image models in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image)
