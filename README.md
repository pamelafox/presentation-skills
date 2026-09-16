# Presentation Skills

Agent skills for presentations — PDFs, slide decks, YouTube recordings, RevealJS, image generation, and GitHub Discussions.

## Why these skills

These skills live in one repo under `.agents/skills/<name>/`. The install script symlinks each skill folder into your agent harness user-scope directory (`ln -sfn`, never copies). Edit a `SKILL.md` here and every project on the machine picks up the change. The same layout works across **omp**, **Claude Code**, **Codex**, and **Pi**, with `gh skill install` and `npx skills add` as registry fallbacks when you prefer package-manager installs.

## The skills (15 + 1 task agent)

| Skill | What it does | Requires |
|---|---|---|
| **pdf-to-markdown** | Convert PDF, PPTX, DOCX, or Excel to Markdown via Microsoft's `markitdown`. | `uv` / `uvx`, `markitdown` |
| **convert-slides-to-images** | Split a PDF into per-slide PNGs (`slide_1.png`, …) with `pdftoppm`. | `uv`, `pdftoppm` (poppler) |
| **extract-slide-text** | Extract per-page text from a PDF into `slide_ascii.md` via `pdftotext`. | `uv`, `pdftotext` (poppler) |
| **make-revealjs-presentation** | Create or update a RevealJS HTML deck from the bundled template in `assets/`. | — |
| **fetch-slides** | Download slides from a URL (PDF, PPTX, OneDrive, RevealJS) and produce `slides.pdf`. | `uv`, LibreOffice (PPTX), Playwright (RevealJS) |
| **review-presentation** | Review slides for accuracy and consistency with repo code samples. | `pdf-to-markdown` skill |
| **outline-slides** | Numbered one-sentence summary per slide image (optionally grounded on `slide_ascii.md`). | slide PNGs from `convert-slides-to-images` |
| **thumbnail-of-pptx** | Screenshot a slide from a OneDrive/Office web viewer link as a clean 16:9 PNG. | `uv`, Playwright |
| **extract-transcript** | Fetch a timestamped transcript from a YouTube video. | `uv` |
| **capture-video-frames** | Download a YouTube video, extract frames at an interval, describe each via the `describe-frame` agent. | `uv`, `yt-dlp`, `ffmpeg`, `describe-frame` agent |
| **youtube-description** | Generate `youtube_description.md` with intro, links, and clickable timestamps. | — |
| **youtube-live-chat** | Download live chat replay from a YouTube video via yt-dlp. | `uv`, `yt-dlp` |
| **generate-writeup** | Orchestrate slides → images → transcript → outline → annotated write-up. | skills above as needed |
| **generate-images-mai** | Generate or edit bitmap images via Microsoft MAI-Image-2.5 (Azure AI). | Python 3.10+, `AZURE_API_KEY`, `AZURE_IMAGE_ENDPOINT` |
| **discussion-commenter** | Post Q&A sections from a markdown writeup as GitHub Discussion comments. | `uv`, `gh` (authenticated) |
| **describe-frame** *(task agent)* | Describe a single video frame or compare speaker-face quality between two frames. Used by `capture-video-frames`. | image-viewing tool (`read` / `viewImage`) |

## Quick install

From the repo root (first run: `chmod +x install.sh` if needed):

```sh
./install.sh all
```

This symlinks all 15 skill folders into each harness's user-scope skills directory. **Symlinks, not copies** — edits here propagate automatically.

## From a local checkout

The repo's native layout (`.agents/skills/<name>/SKILL.md`) is already a discoverable omp skills root when `cwd` points here. Three local-checkout paths, in order of how much state they touch:

### Zero-install (this repo only)

```sh
cd /path/to/presentation-skills
omp
```

omp's `agents` skill provider (priority 70) auto-discovers `.agents/skills/<name>/SKILL.md` from `cwd`. No install step.

### Symlink once, use everywhere (recommended)

```sh
./install.sh omp         # all 15 skills → ~/.omp/agent/skills/<name> (symlinks)
./install.sh omp pdf-to-markdown   # one skill
```

omp discovers skills with `readdir`, which follows directory symlinks — the link at `~/.omp/agent/skills/<name>` resolves to this repo's folder, so every edit here propagates. See the next section for details.

### `omp -e <dir>` (not recommended for this layout)

`omp -e /path/to/presentation-skills` is for plugin-style packages with a `package.json#omp.extensions` entry. The bare `.agents/skills/<name>/SKILL.md` layout here is treated as **skills**, not extensions — `omp -e` won't pick them up. Use the symlink path above instead.

> Background: omp skill discovery (`docs/skills.md`) and extension loading (`docs/extension-loading.md`) are separate subsystems. Symlinking into `~/.omp/agent/skills/` is the documented local-checkout install.

## Per-harness install

### omp

```sh
./install.sh omp
```

Targets `~/.omp/agent/skills/<name>` — one whole-folder symlink per skill. omp's skills provider uses `readdir`, which follows directory symlinks, so new files inside a linked skill folder are discovered without re-running the installer.

omp also auto-discovers `<cwd>/.agents/skills/<name>/SKILL.md` (priority 70) when your working directory is this repo.

The **`describe-frame`** task agent lives at `.github/agents/describe-frame.md`. omp discovers it from the repo cwd (`.github/agents/` group, priority 70). For use in other projects, `./install.sh omp` also symlinks it to `~/.omp/agent/agents/describe-frame.md` when `~/.omp/agent` already exists.

### Claude Code

```sh
./install.sh claude
```

Targets `~/.claude/skills/<name>`. Claude Code discovers skills as subdirectories of `~/.claude/skills/` each containing a `SKILL.md`.

### Codex

```sh
./install.sh codex
```

Targets `${CODEX_HOME:-$HOME/.codex}/skills/<name>`. If `~/.codex` does not exist yet, set `CODEX_HOME` to your Codex config directory and rerun:

```sh
export CODEX_HOME=/path/to/your/codex-home
./install.sh codex
```

### Pi

```sh
./install.sh pi
```

Targets `${PI_CODING_AGENT_DIR:-$HOME/.pi}/skills/<name>`. Same pattern if `~/.pi` is not present:

```sh
export PI_CODING_AGENT_DIR=/path/to/your/pi-home
./install.sh pi
```

## Manual install (no script)

Set `REPO` to this checkout, then symlink one skill per harness:

```sh
REPO=/path/to/presentation-skills

# omp
ln -sfn "$REPO/.agents/skills/pdf-to-markdown" ~/.omp/agent/skills/pdf-to-markdown

# Claude Code
ln -sfn "$REPO/.agents/skills/pdf-to-markdown" ~/.claude/skills/pdf-to-markdown

# Codex
ln -sfn "$REPO/.agents/skills/pdf-to-markdown" "${CODEX_HOME:-$HOME/.codex}/skills/pdf-to-markdown"

# Pi
ln -sfn "$REPO/.agents/skills/pdf-to-markdown" "${PI_CODING_AGENT_DIR:-$HOME/.pi}/skills/pdf-to-markdown"
```

Repeat for each skill name, or loop:

```sh
for d in "$REPO/.agents/skills"/*/; do
  name=$(basename "$d")
  ln -sfn "$d" ~/.omp/agent/skills/"$name"
done
```

## Package-manager fallbacks

These install from upstream registries and typically **copy** files rather than symlink. Prefer `./install.sh` when you want live edits in this repo to propagate.

```sh
# GitHub CLI — pull from this repo's origin (evilbuck) or the upstream mirror (pamelafox)
gh skill install evilbuck/presentation-skills
gh skill install evilbuck/presentation-skills pdf-to-markdown --agent claude-code

# npx skills — same registries
npx skills add evilbuck/presentation-skills
npx skills add evilbuck/presentation-skills/pdf-to-markdown
```

The upstream mirror `pamelafox/presentation-skills` is a regular fetch target; swap `evilbuck` → `pamelafox` in any of the commands above if you want the upstream copy.

## Updating

Edit any file under `.agents/skills/<name>/` — linked installs see the change immediately. When you **add a new skill folder**, rerun `./install.sh` (or `./install.sh <harness>`) so the new symlink is created.

## Uninstalling

```sh
./install.sh uninstall
```

Removes only the symlinks this script created (skill folders and the omp `describe-frame` agent link). It does not delete anything under `.agents/skills/` in the repo.

## Verify

Check symlink status across harnesses:

```sh
./install.sh status
```

Confirm omp sees installed skills:

```sh
omp -p "list every skill you have starting with pdf"
```

You should see `pdf-to-markdown`. Smoke-test a skill:

```sh
omp -p "use pdf-to-markdown to convert slides.pdf to markdown"
```

When working inside this repo without user-scope install, omp also picks up skills from `.agents/skills/` and the `describe-frame` agent from `.github/agents/` via cwd discovery.

## Adding a new skill

1. Create `.agents/skills/<name>/SKILL.md` (and any helper scripts).
2. Run `./install.sh` (or `./install.sh <harness>`).
3. Verify with `./install.sh status` and a harness-specific list command.

No copy step — the symlink points at your new folder.

## Requirements

- **uv** — runs PEP 723 helper scripts (`uv run …`)
- **pdftoppm** / **pdftotext** — poppler (`brew install poppler` on macOS)
- **yt-dlp** and **ffmpeg** — video download and frame extraction
- **Playwright** — `uv run playwright install chromium` for `fetch-slides` and `thumbnail-of-pptx`
- **LibreOffice** — PPTX conversion in `fetch-slides` (`brew install --cask libreoffice` on macOS)
- **markitdown** — pulled via `uvx 'markitdown[pdf]'` for `pdf-to-markdown`
- **gh** — authenticated GitHub CLI for `discussion-commenter`
- **AZURE_API_KEY** and **AZURE_IMAGE_ENDPOINT** — Azure AI image API for `generate-images-mai`

## License

MIT. See [LICENSE](LICENSE).
