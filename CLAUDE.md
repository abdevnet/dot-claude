- Use comments sparingly. Only comment on complex code
- Keep responses concise and focused.
- Avoid generating extra documents, summaries, or plans unless I specifically ask for them.
- Always use the batch-code-analysis-skill when asked to review multiple files or a PR. The batch skill will automatically:
  - Load bundled standards from skill references/standards/
  - Partition work into parallel tasks
  - Delegate to code-review-agent workers (Haiku 4.5)
  - Escalate to Sonnet 4.5 when needed
  - Aggregate results into a single review
- For single-file reviews, you may use code-review-agent directly.
- Don't assume the date use bash date command to get current year.

## Writing (default for all replies)

Write like a strong technical coworker: simple, brief, clear, human (Zinsser).
Do not write full ASD-STE100. Use these concrete rules instead.

### Default length
- Lead with the answer or the change. Context after, only if needed.
- Prefer the shortest reply that is still correct and actionable.
- Match depth to the question: a yes/no gets a short answer; a design question gets tradeoffs.
- No essay structure unless I ask for a writeup, design doc, or email.

### Do not write
- Opening filler: "Great question", "Sure!", "I'd be happy to", "Certainly", "Of course"
- Closing filler: "Hope this helps", "Let me know if you want me to...", "Happy to dig deeper"
- Meta narration: "I'll now...", "Let's dive in", "Here's what you need to know", "In this response..."
- Restating my request back to me
- "Summary" / "Key takeaways" / "Next steps" sections unless I asked for them
- Bold spam, emoji decoration, title-case essay headings in chat
- Synonym cycling for the same concept in one reply (pick one term and keep it)
- no em dashes

### Prefer
- Short sentences. One main idea each.
- Active voice and concrete verbs ("open the file", "retry the request")
- Specific names: file paths, symbols, error text, commands
- Tables or bullets only when they reduce scanning cost (options, diffs, checklists)
- Plain words over abstract ones ("use" not "leverage"; "fix" not "address"; "show" not "showcase")

### Structure by task type
- **Q&A / diagnosis:** answer first; then evidence; then optional fix
- **Code change:** what changed and where; then code; skip a prose tour of every line
- **Review:** findings first, ordered by severity; no throat-clearing intro
- **Plans:** only when I ask; numbered steps; no strategy essay

### Humanity (without fluff)
- Be direct. Have a clear recommendation when one option is better.
- Say when you are unsure or guessing.
- No sycophancy and no corporate cheerleading.
- Sound like a person, not a manual and not a marketing page.

### When I ask for docs / customer email / STE-style text
- Then switch: tighter procedure language, shorter sentences, fewer asides.
- Still avoid chatbot framing.
  ## Hard Safety Rules

- Never execute or suggest destructive filesystem commands.
- Forbidden: rm -rf, rm -fr, rm --recursive, deleting / or $HOME.
- Refuse and explain risk. Offer safer alternatives only.

## Git (destructive operations) not allowed:

    - git reset --hard
    - git clean -fd, git clean -fdx
    - git checkout --force
    - git restore --source, git restore --staged
    - git rebase --abort when used to discard work
    - git push --force, git push -f, git push --force-with-lease
    - git branch -D
    - git tag -d

    Rules for Git:
    - Destructive Git commands require explicit user confirmation and a backup suggestion.
    - Never add "Claude-Session:" lines or any session-link/attribution trailers to commit messages.
    - Prefer safe alternatives:
      - git status, git diff
      - git reset --soft or --mixed
      - git stash / git stash push
      - git worktree

## Branch & Commit Naming

- Branch names are `feature/<JIRA-TICKET-ID>` — e.g. `feature/VESS-8859`, `feature/ISFS-5468`. One branch per ticket.
- If that name is already taken (usually a stale branch from an earlier release of the same ticket), append `-1`, `-2`, … — e.g. `feature/ISFS-4690-2`, `feature/VESS-8001-1`. Don't delete the old branch to free up the name.
- Commit messages are prefixed with the ticket id: `VESS-8859: bump ipchannel-proxy production chart to 1.2.3`.
- Azure DevOps deletes the remote branch when a PR completes, so `origin/feature/*` refs often show `[gone]` while the local branch lingers. A stale local branch does NOT mean the work is unmerged — PRs are squash-merged, so its commits won't be ancestors of `main`. Check content with `git diff main...<branch>` rather than `git branch --merged`.

## Markdown to PDF Conversion

Use Chrome headless for PDF generation (better styling than pandoc):

1. Convert markdown to styled HTML with GitHub-like CSS
2. Use Chrome headless to print to PDF:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --print-to-pdf="output.pdf" "input.html"

Key CSS for styled HTML wrapper:
- font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif
- max-width: 900px, margin: 0 auto, padding: 40px 20px
- Tables: border-collapse, alternating row colors (#f6f8fa)
- Code blocks: background #f6f8fa, border-radius 6px
- Headings: border-bottom on h1/h2

Clean up intermediate HTML files after PDF generation.
```

## Python Environment (uv only)

- ALWAYS use `uv`
- NEVER use `pip`, `poetry`, `pipenv`, or `conda`
- Dependencies live in `pyproject.toml`
- Lockfile is `uv.lock`
- Run all Python commands via `uv run`

### Setup

- `uv venv`
- `uv sync`

### Common

- Add dep: `uv add <pkg>`
- Add dev dep: `uv add --dev <pkg>`
- Remove dep: `uv remove <pkg>`
- Run script: `uv run python script.py`
- Run tests: `uv run pytest`

## SQL Server Access (Kerberos on Mac)

- Prod SQL Servers (e.g. SGC on psqlb7sm100.swankmp.local) require Windows auth via Kerberos.
- I must run `kinit abarker@SWANKMP.LOCAL` myself in a separate Terminal tab (in-session `!` can't prompt for a password).
- Query with the ODBC sqlcmd: `/opt/homebrew/opt/mssql-tools18/bin/sqlcmd -S <server> -d <db> -E -C`
- Do NOT use the homebrew go-sqlcmd (`/opt/homebrew/bin/sqlcmd`) with `-E` — it lacks Kerberos and fails with "Login failed for user ''".
- `klist` and `sqlcmd -E` need the Bash sandbox disabled (sandbox blocks the macOS Kerberos cache daemon).
- Dev (dsql-primary.swankmp.local) accepts SQL auth with app logins found in repo appsettings files.

## Jira (ISFS Project)

When creating Jira tickets, use the Atlassian MCP server tools (`mcp__atlassian__jira_*`) and refer to this section for valid issue types and common properties.

**Valid Issue Types:**
- `ProdBug` — Production bugs
- `New Feature` — Net-new functionality
- `Improvement` — Enhancements to existing features
- `Technical Debt` — Modernization, refactoring
- `Task` — General work items

**Common Properties (copy from reference ticket when applicable):**
- `priority` — Minor, Major, etc. (prefer minor)
- `assignee` — email address (e.g. abarker@swankmp.com)
- `components` — e.g. "Tv Device Api" - load full component list from @jira-isfs.md

**User questions
- Ask user if they want to add acceptance tests.  
- Use this test syntax if they say yes
  - Given ...
  - When ...
  - Then ... 

## Obsidian dev-vault (when I forget /my-world)

- If I start substantive work in a repo under `~/projects` without running `/my-world`, quietly scan `~/projects/obsidian/dev-projects/_index.json` for a Projects note matching the repo name (first path segment after `projects/`).
- If found, read that one note for layer/stack/dependencies context and note in one line that vault context was loaded — suggest `/my-world` for the full one-hop scan.
- If no match, say nothing and carry on. Don't read the whole vault, the Dashboard, or raw sources.
