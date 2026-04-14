# Wiki Lint

Structural health check for the Obsidian dev-projects vault. All work is done in a single bash invocation — no multi-step tool loop.

## How to run

```bash
bash ~/.claude/commands/wiki-lint.sh
```

That's it. One command, one permission prompt. The script is a self-contained Python program that:

1. Walks `Projects/`, `Products/`, `03 - Concepts/`, `01 - Raw Sources/`, `Clippings/` (skipping README.md files)
2. Parses YAML frontmatter and wikilinks in a single pass
3. Runs all 7 structural checks (broken links, asymmetric deps, missing frontmatter, orphans, unprocessed clippings, clippings without relations, one-off tags)
4. Prints a single markdown report to stdout

## What you do

1. Run the command exactly as shown above (do not call individual greps/globs — they were the source of the old permission-prompt spam).
2. Read the script's stdout report verbatim into your response.
3. Summarize the headline counts in 1-2 sentences if appropriate.
4. Ask the user which categories they want to fix. **Do not start fixing anything without explicit approval** — this command is read-only by design.

## Overrides

To point at a different vault:

```bash
WIKI_LINT_VAULT=/path/to/other/vault bash ~/.claude/commands/wiki-lint.sh
```

## Deep mode (semantic checks)

Not yet implemented in the script. When the user asks for `deep` mode, fall back to reading note bodies directly via the Read tool and running these judgment-based checks:

- Duplicate/overlapping concept pages (propose merges)
- Missing concept pages (terms mentioned repeatedly but never extracted)
- Stale project notes (`status: active` but `git log -1 --format=%cr` shows no commits in 90+ days)
- Inconsistent facts about the same entity across notes
- Missing wikilink connections between pages that mention each other

Run these sequentially; they're token-heavy. Always produce a report, never auto-fix.

## Rules

- **Read-only.** Never edit, rename, or delete files during a lint run.
- **One invocation.** Call the `.sh` script; do not reimplement its checks with ad-hoc grep/glob calls.
- **Precise findings.** The script already includes file paths. Preserve them in your response.
- **No auto-fix.** After reporting, ask which findings the user wants to act on.
