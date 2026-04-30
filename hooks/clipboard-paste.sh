#!/bin/bash
# Claude Code UserPromptSubmit hook: clipboard image paste (Windows only).
# On Windows (MSYS/MINGW/Cygwin), forwards stdin to clipboard-paste.ps1
# which reads the clipboard image, saves it, and instructs Claude to Read it.
# On any other OS, exits 0 (no-op) so the same settings.json is portable.

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    script_win=$(cygpath -w "$HOME/.claude/hooks/clipboard-paste.ps1")
    exec pwsh -NoProfile -ExecutionPolicy Bypass -File "$script_win"
    ;;
  *)
    exit 0
    ;;
esac
