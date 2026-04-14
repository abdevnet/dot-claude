# My World

Load context from the Obsidian dev-projects vault scoped to the current project and its direct relationships.

## Instructions

### Step 1 — Identify the current project
Look at the current working directory. Extract the repo name from the path (e.g. `/Users/andybarker/projects/sls/widevine-modular-license-server` → repo is `sls`, or `/Users/andybarker/projects/packager` → repo is `packager`).

### Step 2 — Find the matching project note
Search `/Users/andybarker/projects/obsidian/dev-projects/Projects/` for a `.md` file that matches the current repo name. Match on the `repo` field in the frontmatter or the filename.

### Step 3 — Load context based on what you find

**If a matching project note exists:**
1. Read that project note fully
2. Parse the `depends-on` and `depended-on-by` frontmatter arrays
3. For each linked project (e.g. `[[swankdrm-database]]`), resolve the corresponding `.md` file in the Projects folder and read it
4. Check source control platform:
   - Run `git remote -v` to check the remote URL
   - If the remote points to `swankmp.ghe.com` and the project note does NOT have the `github-enterprise` tag, add it to the tags array
   - If the project has the `github-enterprise` tag, note in the summary that it's on GitHub Enterprise (swankmp.ghe.com); otherwise assume Azure DevOps
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

### Step 4 — Load relevant product data.
Search `/Users/andybarker/projects/obsidian/dev-projects/Products/` look for any product info that may be relevant. Look at the tags for example if in a project folder that contains widevine code look for widevine tags or drm tags.

### Step 5 — Load relevant concepts
Search `/Users/andybarker/projects/obsidian/dev-projects/03 - Concepts/` for pages whose tags or wikilinks overlap with the current project. Match on:
- Shared tags with the project note (e.g. `drm`, `widevine`, `fairplay`, `hls`, `cenc`)
- Pages that contain a wikilink to the current project or any of its directly linked projects/products

Read any matches fully. Concepts are cross-cutting reference knowledge — they often explain the "why" behind what the code does.

### Step 6 — Flag unprocessed raw sources (do not read in full)
Search `/Users/andybarker/projects/obsidian/dev-projects/01 - Raw Sources/` for notes where:
- `processed: false` in frontmatter, AND
- `related` frontmatter array contains a wikilink to the current project, a linked project, or a relevant product

Do **not** read the body of these notes. Just list their titles and source URLs so the user knows there's pending material worth distilling into the wiki for this project. Example output:

> **Unprocessed raw sources (3):** You have 3 clippings related to this project waiting to be distilled — `some-article.md`, `widevine-spec-notes.md`, `team-meeting-2026-04-01.md`. Run the distillation workflow when ready.

If there are none, omit this section entirely.

### Step 7 — Stay scoped
Do not load the full vault. Do not read the Dashboard. Only read:
- The current project note
- Directly linked project notes (one hop only)
- Related product notes
- Related concept notes (tag or wikilink match only)

Raw sources are **listed, not read**.
