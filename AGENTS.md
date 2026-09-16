---
name: presentation-skills
description: "Working guidance for contributing to this repo. Use when adding a new skill, editing existing SKILL.md, modifying helper scripts, running `./install.sh` to install skills at user scope, or packaging this collection for omp / Claude Code / Codex / `gh skill` / `npx skills`."
---

# Presentation Skills (project-local AGENTS.md)

This repo is a **library of agent skills** for working with presentations (PDFs, slide decks, YouTube recordings, RevealJS, MAI image generation, GitHub Discussions). Each skill is a self-contained folder under `.agents/skills/<name>/` containing a `SKILL.md` plus optional Python helper scripts. There is also a task agent at `.github/agents/describe-frame.md` used by the `capture-video-frames` pipeline.

## When to load this file

- Adding, renaming, or deleting a skill
- Editing any `SKILL.md` or its companion script
- Changing the install story for a new harness (omp, Claude Code, Codex, `gh skill`, `npx skills`)
- Wiring up a new task agent under `.github/agents/`

## Repository layout

```
.
├── README.md                          # human install instructions
├── install.sh                         # symlink skills into harness user-scope stores
├── LICENSE                            # MIT
├── .agents/skills/<name>/SKILL.md     # 15 skills
├── .agents/skills/<name>/*.py         # uv-runnable helper scripts
└── .github/agents/describe-frame.md   # task agent invoked by capture-video-frames
```

Every `SKILL.md` is the **only required** artifact. Scripts are referenced as `./<script>.py` inside the skill body and run with `uv run`.

## Goal: portable across projects

The skill set is **meant to be consumed from other projects, not just this repo.** Every skill ships standalone — no project-local state, no per-project config. The author of skill `pdf-to-markdown` should be able to drop the folder into `~/.omp/agent/skills/pdf-to-markdown/` (or any other harness's skill root) and have it work with zero changes. Three rules enforce this:

1. **No shared files between skills.** If two skills need a helper, copy it; never symlink or import across `.agents/skills/<a>` → `.agents/skills/<b>`.
2. **No reads outside the skill directory.** A skill script may read its own files, the user's argument paths, and standard system tools. Anything else (this repo's `README.md`, sibling skills, the user's home dir beyond explicitly-passed paths) is a coupling smell.
3. **Configurable bits go in the user's env, not the skill body.** `generate-images-mai` reads `AZURE_API_KEY` / `AZURE_IMAGE_ENDPOINT`; that's the right pattern. Do not add skill-side `.env` files, `config.toml` lookups, or implicit cwd-relative paths.

When in doubt, ask: *"If I copy this folder into another repo, does it still work?"* If yes, ship it.

## Skill authoring rules (apply to every change)

1. **YAML frontmatter** on every `SKILL.md`:
   - `name:` — kebab-case, must match the directory name (omp falls back to the dir name when missing, but explicit is portable across providers).
   - `description:` — required for native omp discovery (`requireDescription: true`). One or two sentences, written so a model can match it to a user request. Include the `USE FOR:` / `Use when:` trigger phrases verbatim — they are the match surface for model invocation.
   - Optional but supported: `argument-hint:`, `user-invocable:`, `disable-model-invocation:`.
2. **Body**: trigger phrases and examples belong in `description:` and the body. The body is loaded on demand via `skill://<name>` or `/skill:<name>`.
3. **Relative references inside a skill** use `./<script>.py` (relative to the skill directory). omp resolves them via `skill://<name>/<relative-path>`; other harnesses resolve them as plain filesystem paths.
4. **Helper scripts** are PEP 723 inline-metadata Python files (`# /// script ... # ///`). They declare `requires-python` and `dependencies` at the top so `uv run` can resolve them with no virtualenv setup. When adding a dependency, edit the inline metadata block — do not create a separate `requirements.txt` or `pyproject.toml`.
5. **No per-skill `package.json`, no `extensions/` directory, no `commands/`.** This package is skills-only and intentionally portable.

## Task agent

`.github/agents/describe-frame.md` is a read-only agent (`tools: ['read/viewImage']`, `user-invocable: false`) used by `capture-video-frames`. It is the GitHub Agent Skills layout; omp's `agents` provider (priority 70) picks it up automatically. Do not move it to `.agents/agents/` — GitHub Agent Skills expects `.github/agents/`.

## omp installation (portable, cross-project)

The repo uses `.agents/skills/<name>/SKILL.md`, which is the **omp `agents` provider** layout — discovered automatically when running `omp` with `cwd` set to this repo. For use in **other projects**, install into one of omp's native roots so the skills are available everywhere, regardless of cwd.

### Recommended: `./install.sh` (user scope)

From the repo root, symlink skills into omp's user-scope store. This is the default for cross-project use — every `omp` invocation on any machine picks them up.

```sh
./install.sh omp          # all 15 skills → ~/.omp/agent/skills/<name> (symlinks)
./install.sh all          # omp + other harness targets the script supports
./install.sh omp pdf-to-markdown   # one skill only
```

Each installed skill is a symlink at `~/.omp/agent/skills/<name>/` pointing back to this repo's `.agents/skills/<name>/`. Edits here propagate immediately; no reinstall after changes.

> The repo's `.agents/skills/` is already in omp's `agents` provider path, so **if `omp` is launched with `cwd = this repo`, no install is needed at all.** The user-scope symlinks are for when you want the skills in *other* repos without changing `cwd`.

### Per-skill symlink (manual)

```sh
name=pdf-to-markdown
ln -sfn "$(cd .agents/skills/$name && pwd)" "$HOME/.omp/agent/skills/$name"
```

### Project-scoped symlink (another repo)

To make skills auto-discover in a different project without user-scope install:

```sh
name=pdf-to-markdown
mkdir -p /path/to/other-repo/.omp/skills
ln -sfn "$(pwd)/.agents/skills/$name" /path/to/other-repo/.omp/skills/$name
```

### Where omp looks (in precedence order)

| Source root | Priority | Scope | Notes |
|---|---|---|---|
| `~/.omp/agent/skills/<name>/` | 100 (native) | user — **portable across projects** | Survives across every repo on the machine. The right place for skills you reuse. |
| `<cwd>/.omp/skills/<name>/` | 100 (native) | project | Add this if a specific other project wants the skills bundled in-repo. |
| `<this-repo>/.agents/skills/<name>/` (cwd = this repo) | 70 (`agents` provider) | project | Auto-discovered when `cwd` is the repo. Free, no install. |
| Plugin `skills/<name>/` (via `-e` / `extensions:` / `omp plugin link`) | 90 (`omp-plugins`) | depends on plugin | Used when packaging the set as an npm/git plugin. |

### Plugin packaging (optional, only for distribution)

```
presentation-skills/
├── package.json                { "omp": { "extensions": ["./extensions/index.ts"] } }
├── extensions/index.ts         # policy / wiring (optional)
└── skills/<name>/SKILL.md      # rename from .agents/skills/<name>/ (or symlink the whole dir)
```

Symlink note from `omp-extension-authoring-pitfalls`: omp's `skills/` discovery uses `readdir` and **does** follow a whole-directory symlink. So `skills/ -> .agents/skills/` works as a single symlink with zero per-skill maintenance.

### Load-path matrix

| Load path | Loads `omp.extensions`? | Skill namespacing |
|---|---|---|
| `cwd` is this repo (uses `agents` provider) | n/a | bare |
| `--plugin-dir <path>` | **no** | `<dirname>:<skill>` — dev-only |
| `-e <dir>` / `extensions:` in config | yes | bare |
| `omp plugin link <path>` | yes | bare |
| native install (`~/.omp/agent/skills/`) | n/a | bare |

## Adding or modifying a skill

1. Add or edit the skill under `.agents/skills/<name>/` (see authoring rules above).
2. Install or refresh the user-scope symlink: `./install.sh omp <name>` (or `./install.sh omp` / `./install.sh all` for every skill).
3. Because installs are symlinks, further edits in this repo propagate automatically — no copy or reinstall step.

For a brand-new skill, also update the skills table in `README.md` and run `./install.sh omp <name>` so other projects pick it up.

## Other harnesses (cross-platform)

The same `.agents/skills/<name>/` folders load under most Agent Skills–compatible harnesses. Use whichever install command the user already runs; they all end up with the same `SKILL.md` on disk.

- Claude Code: drop the folder under `<repo>/.claude/skills/<name>/` or `~/.claude/skills/<name>/`.
- Codex / Pi: each has its own user-scope skill root; point at `.agents/skills/<name>`.
- `gh skill install`: `gh skill install <owner>/presentation-skills/<name> --agent <harness>`.
- `npx skills add`: `npx skills add <owner>/presentation-skills/<name>` (per-skill or all).

## Verifying a change

After editing any skill:

1. Re-read `SKILL.md` to confirm frontmatter parses (YAML, no tabs).
2. If you touched a script: run it once on a small input to confirm `uv run .agents/skills/<name>/<script>.py …` works.
3. From the repo root: `omp -p "list every skill you have starting with <first-few-chars-of-edited-skill>"`. The edited skill must appear. If it doesn't, your `description:` is too narrow — widen the trigger phrases.
4. **Portability smoke test**: copy the edited skill folder to a temp dir, `cd` somewhere unrelated, and confirm `omp -p "use <skill-name> on …"` still resolves the script via `skill://<name>/<script>.py`. If it fails there, the skill is coupled to this repo and violates rule #2 above.
5. `omp --mode rpc` `get_available_commands` is **only** for slash commands — not skills. Model self-report IS reliable for skills.

## Things to avoid

- Don't add a `tools:` frontmatter restriction without also adding an OMP `tool_call` allow-list gate — omp ignores Claude `tools:` frontmatter, so a restriction advertised in the SKILL.md body is unenforced at runtime.
- Don't `pi.registerCommand()` a name that a file command already owns.
- Don't generalize behavior observed only via `--plugin-dir` to other load paths.
- Don't move scripts out of the skill directory. omp resolves them via the skill's `baseDir`; placing helpers elsewhere breaks `skill://<name>/...` resolution.
- Don't read files from sibling skills, the repo root, or implicit cwd-relative paths. Every cross-project consumer would break.

## See also

- `skill://omp-extension-authoring-pitfalls` — measured omp runtime behaviors to avoid
- `skill://omp-close-parity-gaps-with-extensions` — load-path table and `tool_call` allow-list rationale
- `skill://verify-omp-capability-discovery` — how to probe omp without false negatives
- `skill://cross-platform-pi-omp-loading` — publishing a package that loads under both Pi and omp
- `skill://write-for-agents` — frontmatter and description phrasing that improve skill discovery