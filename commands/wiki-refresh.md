# Wiki Refresh

Update project notes in the dev-projects vault from the commits that landed since each note was last edited. Proposes edits and applies them only after approval.

Arguments: `$ARGUMENTS` (project note names; empty means every note flagged stale)

## 1. Pick the notes

With names, use them. Without, list the flagged notes:

```bash
python3 $HOME/.claude/commands/my-world/scripts/codestate.py stale
```

Staleness is measured against `origin/<default branch>` and only as fresh as the last fetch. If the list shows old `fetched` dates, suggest running `/wiki-lint` first, which fetches the hot repos. If nothing is flagged, say so and stop.

## 2. Gather the change context (one call)

```bash
python3 $HOME/.claude/commands/my-world/scripts/codestate.py context <project> [...]
```

For each note this prints the clone, the default ref, the commits since the note's last edit, a line-count summary, the most-touched files, and the repo's `CLAUDE.md` path if there is one.

## 3. Draft the edits

For each note, read the note and its `CLAUDE.md`, then look at the real changes behind the commits that matter. Use `git -C <clone> show <sha>`, or `git -C <clone> diff <sha>^..<ref> -- <path>` for the most-touched files. Commit subjects alone aren't enough to rewrite a fact.

With 3 or more notes, give each to its own general-purpose subagent in parallel. Pass along the context block and the rules below, and ask for back either "no change needed" with a one-line reason, or a list of exact old/new text replacements for the note.

Rules for edits:
- Change only facts the commits show: endpoints, tables, config, dependencies, deployment, active work, gotchas. Leave the hand-written "why", history, and structure alone.
- Don't paste commit logs into the note. Fold changes into the sections they belong to. A short `## Active work` bullet with the ticket ID is fine for work in progress.
- If a dependency is added or removed, update `depends-on` in this note and `depended-on-by` in the other note, so `/wiki-lint` stays clean.
- Mark guesses as guesses. When unsure, leave the fact as it is and mention it.
- Get today's date with `date +%F`, not from memory.

## 4. Review, then apply

Show the proposals together: for each note, a short diff plus the commits that justify it. Ask which to apply: all, some, or none. Don't edit anything before the user answers.

On approval:
- Apply the edits with Edit.
- For notes reviewed with "no change needed", add or update `verified: <today>` in the frontmatter, so the note stops showing as stale until new commits land. Apply this only with the same approval.

Editing a note updates its modification time, which clears the stale flag. The `/my-world` index rebuilds itself on the next run.

## Rules

- Never pull, check out, or change anything in the code repos. Read only: `git log`, `show`, `diff`.
- Only edit vault notes the user approved.
