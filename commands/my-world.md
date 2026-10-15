# My World

Load the slice of the Obsidian dev-projects vault that the current task touches: a map of the whole system, plus full notes for the projects, concepts, and products closest to the task. The goal is architect-level context across repos, not just the current one.

Arguments: `$ARGUMENTS`

## Run the resolver (one call)

```bash
python3 $HOME/.claude/commands/my-world/scripts/resolve.py --cwd "$PWD" [--budget N] [name ...] ["task text"]
```

Build the call from the arguments:
- `fast` → `--budget 30k`. `deep` → `--budget 200k`. Default budget is 100k tokens.
- Project, concept, or product names (e.g. `sls tv-device-api`) → separate arguments. Each becomes a seed.
- Anything else → one quoted task string. Words in it that name a note also become seeds; the rest rank notes by keyword.
- No arguments, but the conversation already describes a task → pass a short task phrase anyway. It sharpens the ranking.

The working directory is also a seed: the first path segment after `projects/` is the repo name, so a worktree like `.../sls/fairplay-sdk26` resolves to `sls`.

## What the output contains

- `#` header lines: budget used, seeds and why, task terms, hubs, unresolved links, loaded/omitted counts, and source control when the working directory is a repo.
- `===== SYSTEM MAP =====`: every project with layer, one-line overview, and depends-on, plus concept and product one-liners. Use it to reason about anything outside the loaded slice.
- `===== PROJECT|CONCEPT|PRODUCT [full|card] score · reason: path =====`: notes in rank order. Seeds and one-hop neighbours come in full; two-hop and keyword or tag matches come in full if budget allows, otherwise as cards (frontmatter + overview). Read a card's path when you need the whole note.
- `> code:` line under each project note: local clone path, checked-out branch, last commit on `origin/<default>`, when origin was last fetched, when the note was edited (or `verified:`), non-merge commits on `origin/<default>` since then, and whether a `CLAUDE.md` exists. `POSSIBLY STALE` means 5+ commits landed after the note's last edit; the header lists these notes. An old fetch date means the count may be low; `/wiki-lint` fetches hot repos and `/wiki-refresh` updates stale notes.
- `===== UNPROCESSED RAW SOURCES =====`: listing only, if any relate to loaded notes.
- `===== OMITTED =====`: relevant notes that didn't fit. Read them on demand.

Hubs (heavily linked shared infra such as `gitops` and `databases-sgc`) are loaded but not walked through, so two hops stays focused.

Sentinels:
- `# NO_SEED` → only the map loaded. If the working directory is a real repo, say there's no project note for it and offer to create one (load the `obsidian:obsidian-markdown` skill first if they accept). Otherwise ask which projects or task to scope to, using the map to suggest likely ones.
- `# unmatched names` → say which names had no note; they were treated as keywords.

## Reply

Everything loaded is already in context, so don't retell it note by note. Keep the reply to about 25 lines:

1. **Loaded:** one line with the seeds, full/card counts, and budget used.
2. **Slice:** the seeds and their direct neighbours as a short dependency sketch, one line each on why each matters here.
3. **What matters for the task:** 3–6 bullets of specific facts, risks, or touchpoints drawn from the notes (tables, contracts, active work, gotchas). With no task, flag the seed note's active work and gotchas instead.
4. **Gaps:** stale notes the task relies on, unresolved links, omitted notes worth reading, raw sources waiting to be distilled. Skip this section if there are none.

Vault notes describe intent and can lag the code. When the task leans on a stale note, check the repo before trusting it: read its `CLAUDE.md` and `git log --oneline --no-merges --since=<note edited date>` in the clone path. If the code has moved on from the note, offer to update the note. A missing `CLAUDE.md` is worth mentioning only when the task will work inside that repo.

## Fallback

If the resolver fails, the index is `$HOME/projects/obsidian/dev-projects/_index.json` (query with `jq`) and the notes live in `Projects/`, `Products/`, `03 - Concepts/`, and `01 - Raw Sources/`. Rebuild the index with `python3 $HOME/.claude/commands/my-world/scripts/build_index.py`.
