# My World

Load context from the Obsidian dev-projects vault scoped to the current project and its direct relationships.

## Mode

Arguments: `$ARGUMENTS`

- If arguments contain `fast`, run in **fast mode**.
- Otherwise, run in **full mode**.

**Fast mode** loads only the current project note and its one-hop dependencies. It skips Products, Concepts, and Raw Sources scans, and skips the `git remote` verification.  Use it when you want quick orientation without broader cross-cutting context.

**Full mode** does everything below.

## Instructions

### Step 0 — Index preflight
The vault has a JSON index at `/Users/andybarker/projects/obsidian/dev-projects/_index.json` that lets Steps 2/4/5/6 be answered with `jq` queries instead of folder scans. The index is self-healing — the preflight rebuilds it when it's missing or stale.

```bash
INDEX=/Users/andybarker/projects/obsidian/dev-projects/_index.json
VAULT=/Users/andybarker/projects/obsidian/dev-projects
BUILD=/Users/andybarker/.claude/commands/my-world/scripts/build_index.py
SCHEMA=1

stale=0
if [ ! -f "$INDEX" ]; then
  stale=1
elif [ -n "$(find "$VAULT" -name '*.md' -newer "$INDEX" -print -quit 2>/dev/null)" ]; then
  stale=1
elif [ -n "$(find "$VAULT" -type d -newer "$INDEX" -print -quit 2>/dev/null)" ]; then
  stale=1
elif [ "$(jq -r '.schema_version // 0' "$INDEX" 2>/dev/null)" != "$SCHEMA" ]; then
  stale=1
fi

if [ "$stale" = "1" ]; then
  python3 "$BUILD" && echo INDEX_READY || echo INDEX_FAILED
else
  echo INDEX_READY
fi
```

- `INDEX_READY` → use the **indexed queries** shown under each step.
- `INDEX_FAILED` → use the **grep fallback** shown under each step and mention in the summary that the index rebuild failed.

The `find -newer` checks catch added/modified .md files *and* folder-level changes (adds/deletes bump directory mtime). A `schema_version` mismatch forces a rebuild when this script evolves.

### Step 1 — Identify the current project
Look at the current working directory. Extract the repo name from the path (e.g. `/Users/andybarker/projects/sls/widevine-modular-license-server` → repo is `sls`, or `/Users/andybarker/projects/packager` → repo is `packager`).

### Step 2 — Find the matching project note
Match on the `repo` frontmatter field (which may be a bare name or a path like `~/projects/packager`) or the filename.

**Indexed query:**
```bash
jq -r --arg repo "$REPO" '
  .notes[]
  | select(.folder == "Projects")
  | select(.title == $repo or .repo == $repo or ((.repo // "") | split("/") | last) == $repo)
  | .file
' "$INDEX"
```

**Grep fallback:**
```bash
grep -rl "^repo:.*\\b$REPO\\b" /Users/andybarker/projects/obsidian/dev-projects/Projects/ 2>/dev/null
# plus filename match:
find /Users/andybarker/projects/obsidian/dev-projects/Projects -maxdepth 1 -iname "$REPO.md"
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
- If the user accepts, invoke the `obsidian:obsidian-markdown` skill before writing the file so frontmatter, tags, wikilinks, and any callouts are valid OFM

**If there are no `depends-on` or `depended-on-by` links:**
- Load only the current project note
- Say: "No linked projects found — loaded context for `<repo-name>` only."

---

**Fast mode stops here.** Skip Steps 4–6 and go straight to Step 7.

---

### Step 4 — Load relevant product data
Find product notes whose tags overlap with the current project's tags (e.g. widevine, drm, fairplay), then read matches in a single batched tool call.

**Indexed query** (substitute the project's tags):
```bash
jq -r --argjson tags '["widevine","drm","fairplay"]' '
  .notes[]
  | select(.folder == "Products")
  | select((.tags // []) | any(. as $t | $tags | index($t)))
  | .file
' "$INDEX"
```

**Grep fallback:**
```bash
grep -rl -E "^  - (widevine|drm|fairplay)$" /Users/andybarker/projects/obsidian/dev-projects/Products/ 2>/dev/null
```

### Step 5 — Load relevant concepts
Find concepts that overlap with the current project on **either** shared tags **or** wikilinks pointing at the current project or its linked projects/products.

**Indexed query** (substitute project tags and linked names):
```bash
jq -r \
  --argjson tags '["drm","widevine","fairplay","hls","cenc"]' \
  --argjson links '["packager","swankdrm-database","shaka-packager"]' '
  .notes[]
  | select(.folder == "03 - Concepts")
  | select(
      ((.tags // []) | any(. as $t | $tags | index($t)))
      or
      ((.wikilinks // []) | any(. as $w | $links | index($w)))
    )
  | .file
' "$INDEX"
```

**Grep fallback:**
```bash
# Tag overlap
grep -rl -E "^  - (tag1|tag2|tag3)$" "/Users/andybarker/projects/obsidian/dev-projects/03 - Concepts/" 2>/dev/null
# Wikilink to current or linked project/product
grep -rlF -e "[[<current>]]" -e "[[<dep1>]]" -e "[[<dep2>]]" "/Users/andybarker/projects/obsidian/dev-projects/03 - Concepts/" 2>/dev/null
```

Union the candidates, then read all matches in a single batched tool call. Concepts are cross-cutting reference knowledge — they often explain the "why" behind what the code does. If the candidate list is large (>8), prefer concepts that share **2+ tags** with the project over single-tag matches.

### Step 6 — Flag unprocessed raw sources (do not read bodies)
Surface notes where `processed: false` and the `related` array points at the current project, a linked project, or a relevant product.

**Indexed query** (substitute linked names):
```bash
jq -r --argjson links '["packager","swankdrm-database","shaka-packager"]' '
  .notes[]
  | select(.folder == "01 - Raw Sources" and .processed == false)
  | select((.related // []) | any(. as $r | $links | index($r)))
  | .file
' "$INDEX"
```

**Grep fallback:**
```bash
{ grep -rl "^processed: false$" "/Users/andybarker/projects/obsidian/dev-projects/01 - Raw Sources/" \
    | xargs grep -lF -e "[[<current>]]" -e "[[<dep1>]]"; } 2>/dev/null || true
```

`grep` exits 1 when it finds nothing — that's normal, not an error. The `|| true` swallows that benign exit (and the downstream empty-input case) so the transcript stays clean.

Do **not** read the body. Just list titles and source URLs. Example output:

> **Unprocessed raw sources (3):** You have 3 clippings related to this project waiting to be distilled — `some-article.md`, `widevine-spec-notes.md`, `team-meeting-2026-04-01.md`. Run the distillation workflow when ready.

If there are none, omit this section entirely.

### Step 7 — Stay scoped
Do not load the full vault. Do not read the Dashboard. Only read:
- The current project note
- Directly linked project notes (one hop only)
- **Full mode only:** related product notes, related concept notes (tag or wikilink match), and a listing (not bodies) of unprocessed raw sources
