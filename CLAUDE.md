- Use comments sparingly. Only comment on complex code
- Keep responses concise and focused.
- Avoid generating extra documents, summaries, or plans unless I specifically ask for them.
- Always use the batch-code-analysis-skill when asked to review multiple files or a PR. The batch skill will automatically:
  - Load standards from ~/projects/ai-instructions/
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

@RTK.md
