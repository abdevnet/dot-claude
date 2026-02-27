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
4. Summarize what you loaded:
   - Current project: name, layer, stack, repo
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

### Step 4 — Stay scoped
Do not load the full vault. Do not read the Dashboard. Only read: the current project note + its directly linked project notes (one hop only).
