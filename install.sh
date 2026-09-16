#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/.agents/skills"
AGENT_SRC="$SCRIPT_DIR/.github/agents/describe-frame.md"
CMD="${1:-all}"

case "$CMD" in
  omp)    TARGET_ROOT="$HOME/.omp/agent/skills" ;;
  claude) TARGET_ROOT="$HOME/.claude/skills" ;;
  codex)  TARGET_ROOT="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  pi)     TARGET_ROOT="${PI_CODING_AGENT_DIR:-$HOME/.pi}/skills" ;;
  all)    TARGET_ROOT="ALL" ;;
  uninstall|status) TARGET_ROOT="$CMD" ;;
  *) echo "Usage: $0 {omp|claude|codex|pi|all|uninstall|status}"; exit 2 ;;
esac

target_for() {
  case "$1" in
    omp)    printf '%s\n' "$HOME/.omp/agent/skills" ;;
    claude) printf '%s\n' "$HOME/.claude/skills" ;;
    codex)  printf '%s\n' "${CODEX_HOME:-$HOME/.codex}/skills" ;;
    pi)     printf '%s\n' "${PI_CODING_AGENT_DIR:-$HOME/.pi}/skills" ;;
    *)      return 1 ;;
  esac
}

harness_home() {
  case "$1" in
    codex) printf '%s\n' "${CODEX_HOME:-$HOME/.codex}" ;;
    pi)    printf '%s\n' "${PI_CODING_AGENT_DIR:-$HOME/.pi}" ;;
    *)     return 1 ;;
  esac
}

should_skip_harness() {
  local harness="$1"
  case "$harness" in
    codex|pi)
      local home var
      home="$(harness_home "$harness")"
      if [[ ! -d "$home" ]]; then
        var=$([[ "$harness" == "codex" ]] && echo "CODEX_HOME" || echo "PI_CODING_AGENT_DIR")
        echo "INFO: skipping ${harness} (target root not found, set ${var})"
        return 0
      fi
      ;;
  esac
  return 1
}

link_one() {
  local target_root="$1"
  local harness="$2"

  mkdir -p "$target_root"
  for d in "$SRC"/*/; do
    [[ -d "$d" ]] || continue
    local name
    name="$(basename "$d")"
    ln -sfn "$d" "$target_root/$name"
    echo "linked ${name} -> ${target_root}/${name}"
  done

  if [[ "$harness" == "omp" && -d "$HOME/.omp/agent" ]]; then
    local agents_dir="$HOME/.omp/agent/agents"
    mkdir -p "$agents_dir" 2>/dev/null || true
    if [[ -d "$agents_dir" && -f "$AGENT_SRC" ]]; then
      ln -sfn "$AGENT_SRC" "$agents_dir/describe-frame.md"
      echo "linked describe-frame.md -> ${agents_dir}/describe-frame.md"
    fi
  fi
}

unlink_one() {
  local target_root="$1"
  local harness="$2"

  for d in "$SRC"/*/; do
    [[ -d "$d" ]] || continue
    local name
    name="$(basename "$d")"
    rm -f "$target_root/$name"
    echo "removed ${target_root}/${name}"
  done

  if [[ "$harness" == "omp" ]]; then
    rm -f "$HOME/.omp/agent/agents/describe-frame.md"
    echo "removed ${HOME}/.omp/agent/agents/describe-frame.md"
  fi
}

status_one() {
  local target_root="$1"
  local harness="$2"

  echo "== ${harness} (${target_root}) =="
  for d in "$SRC"/*/; do
    [[ -d "$d" ]] || continue
    local name link dest
    name="$(basename "$d")"
    link="${target_root}/${name}"
    if [[ -L "$link" ]]; then
      dest="$(readlink "$link")"
      if [[ -e "$link" ]]; then
        echo "  OK       ${link} -> ${dest}"
      else
        echo "  BROKEN   ${link} -> ${dest}"
      fi
    elif [[ -e "$link" ]]; then
      echo "  COPY     ${link} (not a symlink)"
    else
      echo "  MISSING  ${link}"
    fi
  done

  if [[ "$harness" == "omp" ]]; then
    local agent_link="${HOME}/.omp/agent/agents/describe-frame.md"
    if [[ -L "$agent_link" ]]; then
      dest="$(readlink "$agent_link")"
      if [[ -e "$agent_link" ]]; then
        echo "  OK       ${agent_link} -> ${dest}"
      else
        echo "  BROKEN   ${agent_link} -> ${dest}"
      fi
    elif [[ -e "$agent_link" ]]; then
      echo "  COPY     ${agent_link} (not a symlink)"
    else
      echo "  MISSING  ${agent_link}"
    fi
  fi
}

install_harness() {
  local harness="$1"
  if should_skip_harness "$harness"; then
    return 0
  fi
  local target_root
  target_root="$(target_for "$harness")"
  echo "== ${harness} =="
  link_one "$target_root" "$harness"
}

case "$CMD" in
  all)
    for harness in omp claude codex pi; do
      install_harness "$harness"
    done
    ;;
  uninstall)
    for harness in omp claude codex pi; do
      if should_skip_harness "$harness"; then
        continue
      fi
      target_root="$(target_for "$harness")"
      echo "== ${harness} =="
      unlink_one "$target_root" "$harness"
    done
    ;;
  status)
    for harness in omp claude codex pi; do
      if should_skip_harness "$harness"; then
        continue
      fi
      target_root="$(target_for "$harness")"
      status_one "$target_root" "$harness"
    done
    ;;
  *)
    install_harness "$CMD"
    ;;
esac
