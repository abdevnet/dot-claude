# My World

Load context from the Obsidian dev-projects vault scoped to the current project and its direct relationships.

## Mode

Arguments: `$ARGUMENTS`

- If arguments contain `fast`, run in **fast mode**.
- Otherwise, run in **full mode**.

**Fast mode** loads only the current project note and its one-hop dependencies. It skips Products, Concepts, and Raw Sources scans, and skips the `git remote` verification. Use it when you want quick orientation without broader cross-cutting context.

**Full mode** additionally loads related Products and Concepts, lists unprocessed Raw Sources, and resolves the source-control platform.

Both modes are served by one resolver script — `scripts/resolve.py` — so the whole data-gather is a single tool call. The latency that hurts here is the model waiting on sequential round-trips (the old flow was index-preflight → jq match → batched Reads), not the shell work, which is sub-100ms. Collapsing to one call is the win.

## Fast mode (single call)

```bash
python3 $HOME/.claude/commands/my-world/scripts/resolve.py "$PWD"
```

Given the working directory, this self-heals the index if a vault note changed, matches the project note (the first path segment after `projects/` is the repo name, so a worktree like `.../sls/fairplay-sdk26` still resolves to `sls`), and prints the project note's body plus the body of every depends-on / depended-on-by project, each under a `===== LABEL: path =====` delimiter. Read stdout and write the summary directly — no Reads, no jq, no `git remote` check.

Handle the leading `#` status lines and these sentinels:
- `NO_PROJECT_NOTE …` → say "No project note found for `<repo-name>` in the dev-projects vault. You may want to add one," offer to create it (invoke the `obsidian:obsidian-markdown` skill first if they accept), and stop.
- `# NO_LINKS …` → summarize just the current project and say "No linked projects found — loaded context for `<repo-name>` only."

Then produce the summary (below) and stop.

## Full mode (single call)

```bash
python3 $HOME/.claude/commands/my-world/scripts/resolve.py "$PWD" --full
```

Same as fast mode, plus three extra sections in the same output:
- `# source-control:` — GitHub Enterprise (from the note's `github-enterprise` tag, or a detected `swankmp.ghe.com` remote) vs Azure DevOps / other. If it reports a `swankmp.ghe.com` remote and the note lacks the tag, mention that the tag could be added.
- `===== PRODUCTS … =====` — product notes whose tags overlap the project's tags. Summarize each.
- `===== CONCEPTS … =====` — concept notes sharing tags with the project **or** wikilinking to the project / a linked project / a matched product. They're ordered by relevance (wikilink match first, then shared-tag count) and annotated with both. Concepts are cross-cutting "why" knowledge — weave the relevant ones into the summary. If the header notes that weaker single-tag matches were dropped, that's the >8-candidate trim; no action needed.
- `===== UNPROCESSED RAW SOURCES (N) =====` — a listing (title — source URL — related), **not** bodies. Surface these as a "waiting to be distilled" note if N > 0; omit the section entirely if 0.

## Summary structure

Both modes end with a summary covering:
- **Current project**: name, layer, stack, repo (full mode: source-control platform too)
- **Dependencies** (depends-on): list with a one-line description of each
- **Dependents** (depended-on-by): list with a one-line description of each
- **Full mode**: relevant Products and Concepts woven in, plus the unprocessed-raw-sources flag if any
- Any notes or key details from the current project note worth flagging

## Stay scoped

The resolver only ever loads one hop out (the project, its direct links, and — in full mode — tag/wikilink-matched products and concepts, plus a raw-source listing). Don't read the full vault or the Dashboard, and don't read raw-source bodies.

## Fallback

If the resolver errors out (e.g. Python unavailable), the equivalent data lives in the index at `$HOME/projects/obsidian/dev-projects/_index.json` and can be queried with `jq`, or grepped directly from the vault folders (`Projects/`, `Products/`, `03 - Concepts/`, `01 - Raw Sources/`). Rebuild the index with `python3 $HOME/.claude/commands/my-world/scripts/build_index.py`.
