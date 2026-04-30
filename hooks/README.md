# Claude Code Hooks

## clipboard-paste — Windows clipboard image paste

Workaround for the broken native `chat:imagePaste` action on Windows
(see [issue #54902](https://github.com/anthropics/claude-code/issues/54902)
and [issue #38807](https://github.com/anthropics/claude-code/issues/38807)).

### How it works

A `UserPromptSubmit` hook runs on every prompt. When the prompt contains
the word `paste` (case-insensitive, word-boundary match), the hook:

1. Reads the bitmap from the Windows clipboard via
   `[System.Windows.Forms.Clipboard]::GetImage()`.
2. Saves it as `~/.claude/clipboard/clip_<timestamp>.png`.
3. Emits an instruction on stdout telling Claude to call the `Read` tool
   on that exact path. `Read` handles PNG natively as multimodal input,
   so the image becomes part of Claude's context.
4. Prunes any clip files older than 30 days.

If no image is on the clipboard, the hook writes a notice to stderr and
exits 0 (the prompt still goes through unchanged).

### Files

- `clipboard-paste.sh` — bash wrapper. On Mac/Linux it's a no-op
  (`exit 0`); on Windows (MSYS/MINGW/Cygwin) it forwards stdin to the
  PowerShell script. This lets the same `settings.json` work on both
  Windows and Mac without per-machine overrides.
- `clipboard-paste.ps1` — actual logic. Runs under `pwsh` 7+ or
  Windows PowerShell 5.1.

### Usage

1. Win+Shift+S to snip a screenshot (puts a bitmap on the clipboard).
2. Type a prompt that contains `paste` somewhere, e.g.
   `what does this show? paste`.
3. Submit. The hook fires, saves the PNG, and Claude reads it before
   responding.

### Settings registration

In `~/.claude/settings.json`:

```json
"hooks": {
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/clipboard-paste.sh"
        }
      ]
    }
  ]
}
```

### Tightening the trigger

The default regex `\bpaste\b` matches any prompt mentioning the word
"paste" — including phrases like "let me paste this code". If false
positives become a problem, edit the regex in `clipboard-paste.ps1`:

- Trailing-only:  `(?i)\bpaste\b\s*[!.?]*\s*$`
- Sigil:          `:paste\b` (then type prompts like `... :paste`)

### Removing native imagePaste once Anthropic fixes it

When the `chat:imagePaste` action starts working on Windows, this hook
becomes redundant. Remove it by deleting the `UserPromptSubmit` entry
from `settings.json`; the script files can stay or be deleted.
