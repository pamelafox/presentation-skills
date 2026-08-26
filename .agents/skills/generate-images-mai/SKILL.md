---
name: generate-images-mai
description: 'Generate bitmap images from text prompts with Microsoft MAI-Image-2.5 through the Azure AI image generations API. Use when asked to create, render, illustrate, or generate an image, visual asset, photograph, background, poster, thumbnail, or concept art with Microsoft Image 2.5 or MAI-Image-2.5.'
argument-hint: 'Describe the image and optionally provide output path, width, and height'
user-invocable: true
disable-model-invocation: false
---

# Generate images with MAI-Image-2.5

Create an image from a text description, save it to the user's requested location, and verify that the resulting file is usable.

## Requirements

- Python 3.10+.
- A `.env` file in the current directory or one of its parents:
```dotenv
AZURE_API_KEY=your-key
AZURE_IMAGE_ENDPOINT=https://your-resource.services.ai.azure.com/mai/v1/images/generations
```

Never read, print, return, commit, or embed the API key in generated files, commands, logs, or chat. Do not create a `.env` containing a real secret. If configuration is missing, tell the user which variable to add without asking them to send its value through chat.

## Procedure

1. Determine the requested subject, intended use, output path, dimensions, and visual constraints from the conversation.
2. If the prompt is underspecified, preserve the user's intent and add only useful visual detail: medium, composition, environment, lighting, palette, camera or rendering style, and important exclusions. Do not introduce brands, people, text, or sensitive attributes the user did not request.
3. Default to `1024x1024` and `generated_image.png` when dimensions or output path are absent. Use the user's requested dimensions without inventing API restrictions.
4. Run [generate_image.py](./scripts/generate_image.py) with the refined prompt. Pass arguments as separate shell tokens and quote all user-provided values.

```bash
python3 .agents/skills/generate-images-mai/scripts/generate_image.py \
  --prompt "A photograph of a red fox in an autumn forest" \
  --width 1024 \
  --height 1024 \
  --output generated_image.png
```

5. If the destination exists, do not overwrite it unless the user explicitly requested replacement; use a new descriptive filename or pass `--force` only with that permission.
6. Verify the output exists, is non-empty, and can be decoded as an image. Use the image-viewing tool to inspect it when available.
7. Check that the result matches the requested subject, composition, dimensions, legibility, and safety constraints. Regenerate with a targeted prompt adjustment when the image is blank, malformed, materially off-topic, or has obvious layout defects.
8. Report the saved path and final dimensions. Mention prompt changes only when they materially affect the user's request.

## Options

The script supports:

- `--prompt`: required image description.
- `--output`: output file path; defaults to `generated_image.png`.
- `--width` and `--height`: positive integers; default to `1024`.
- `--model`: model name; defaults to `MAI-Image-2.5`.
- `--endpoint`: Azure image generations endpoint; overrides `AZURE_IMAGE_ENDPOINT`.
- `--env-file`: loads a specific `.env` file instead of searching parent directories.
- `--force`: permits replacing an existing output file.

Environment variables already present in the process take precedence over values in `.env`.

## Failure handling

- Missing configuration: identify `AZURE_API_KEY` or `AZURE_IMAGE_ENDPOINT` and stop.
- HTTP authentication failure: tell the user to verify `AZURE_API_KEY` locally; never request the key in chat.
- HTTP endpoint or deployment failure: report the status and sanitized API message, then verify the endpoint and model name.
- Invalid or absent `b64_json`: do not create an output file; report the response-shape problem.
- Content-policy rejection: explain that the service rejected the prompt and offer a compliant revision.
- Corrupt or empty image: remove the incomplete output and retry once with the same request before changing the prompt.

## Completion checks

- The secret was not exposed.
- The requested output was created without overwriting unrelated work.
- The file is a decodable image with the requested dimensions.
- Visual inspection confirms the primary subject and layout are present.
- The user receives a clickable path to the image.