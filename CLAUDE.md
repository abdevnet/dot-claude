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

