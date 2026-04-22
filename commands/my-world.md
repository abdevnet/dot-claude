# My World

Load context from the Obsidian dev-projects vault scoped to the current project and its direct relationships.

## Mode

Arguments: `$ARGUMENTS`

- If arguments contain `fast`, run in **fast mode**.
- Otherwise, run in **full mode**.

**Fast mode** loads only the current project note and its one-hop dependencies. It skips Products, Concepts, and Raw Sources scans, and skips the `git remote` verification.  Use it when you want quick orientation without broader cross-cutting context.

**Full mode** does everything below.

## Instructions

### Step 1 — Identify the current project
Look at the current working directory. Extract the repo name from the path (e.g. `/Users/andybarker/projects/sls/widevine-modular-license-server` → repo is `sls`, or `/Users/andybarker/projects/packager` → repo is `packager`).

### Step 2 — Find the matching project note
Search `/Users/andybarker/projects/obsidian/dev-projects/Projects/` for a `.md` file that matches the current repo name. Match on the `repo` field in the frontmatter or the filename.

Prefer `grep -l` over reading candidates one-by-one. Example:

```bash
grep -rl "^repo: *<repo-name>$" /Users/andybarker/projects/obsidian/dev-projects/Projects/
```

### Step 3 — Load the project note and linked projects
1. Read the matching project note.
2. Parse the `depends-on` and `depended-on-by` frontmatter arrays.
3. Resolve each `[[wikilink]]` to a `.md` file in the Projects folder and **read all of them in a single batched tool call** (parallel, not sequential).
4. Check source control platform:
   - If the project note already has the `github-enterprise` tag, skip the remote check and note GitHub Enterprise (swankmp.ghe.com) in the summary.
   - Otherwise run `git remote -v`. If the remote points to `swankmp.ghe.com`, add `github-enterprise` to the tags array and note the platform; otherwise assume Azure DevOps.
5. Summarize what you loaded:
   - Current project: name, layer, stack, repo, source control platform
   - Dependencies (depends-on): list with one-line description of each
   - Dependents (depended-on-by): list with one-line description of each
   - Any notes or key details from the current project note worth flagging

**If NO matching project note exists:**
- Say: "No project note found for `<repo-name>` in the dev-projects vault. You may want to add one."
- Do not load anything else
- Offer to create the project note if the user wants

**If there are no `depends-on` or `depended-on-by` links:**
- Load only the current project note
- Say: "No linked projects found — loaded context for `<repo-name>` only."

---

**Fast mode stops here.** Skip Steps 4–6 and go straight to Step 7.

---

### Step 4 — Load relevant product data
Search `/Users/andybarker/projects/obsidian/dev-projects/Products/` for product notes whose tags overlap with the current project (e.g. widevine, drm, fairplay).

Use `grep -l` to get candidate filenames first, then read only matches in a single batched tool call:

```bash
grep -rl -E "^  - (widevine|drm|fairplay)$" /Users/andybarker/projects/obsidian/dev-projects/Products/
```

Substitute the tag list with the tags from the current project note.

### Step 5 — Load relevant concepts
Search `/Users/andybarker/projects/obsidian/dev-projects/03 - Concepts/` for pages that overlap with the current project. Match on:
- Shared tags with the project note (e.g. `drm`, `widevine`, `fairplay`, `hls`, `cenc`)
- Pages that contain a wikilink to the current project or any of its directly linked projects/products

Use two `grep -l` passes to build a candidate list without loading bodies:

```bash
# Tag overlap
grep -rl -E "^  - (tag1|tag2|tag3)$" /Users/andybarker/projects/obsidian/dev-projects/03\ -\ Concepts/

# Wikilink to current or linked project/product
grep -rlF -e "[[<current>]]" -e "[[<dep1>]]" -e "[[<dep2>]]" /Users/andybarker/projects/obsidian/dev-projects/03\ -\ Concepts/
```

Union the two candidate lists, then read all matches in a single batched tool call. Concepts are cross-cutting reference knowledge — they often explain the "why" behind what the code does.

If the candidate list is large (>8), prefer concepts that share **2+ tags** with the project over single-tag matches.

### Step 6 — Flag unprocessed raw sources (do not read bodies)
Search `/Users/andybarker/projects/obsidian/dev-projects/01 - Raw Sources/` for notes where:
- `processed: false` in frontmatter, AND
- `related` frontmatter array contains a wikilink to the current project, a linked project, or a relevant product

Use `grep -l` on `processed: false` to get candidates, then a second grep over those candidates for the wikilink:

```bash
{ grep -rl "^processed: false$" "/Users/andybarker/projects/obsidian/dev-projects/01 - Raw Sources/" \
    | xargs grep -lF -e "[[<current>]]" -e "[[<dep1>]]"; } 2>/dev/null || true
```

`grep` exits 1 when it finds nothing — that's normal, not an error. The `|| true` suppresses that benign exit so the transcript stays clean, and it also covers the case where the first `grep` returns zero candidates (the downstream `xargs grep` then reads EOF and exits 1).

Do **not** read the body. Just list titles and source URLs. Example output:

> **Unprocessed raw sources (3):** You have 3 clippings related to this project waiting to be distilled — `some-article.md`, `widevine-spec-notes.md`, `team-meeting-2026-04-01.md`. Run the distillation workflow when ready.

If there are none, omit this section entirely.

### Step 7 — Stay scoped
Do not load the full vault. Do not read the Dashboard. Only read:
- The current project note
- Directly linked project notes (one hop only)
- **Full mode only:** related product notes, related concept notes (tag or wikilink match), and a listing (not bodies) of unprocessed raw sources
