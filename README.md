A collection of skills, agents, commands, hooks, and a statusline for Claude Code.

To use, clone this repo into your local `.claude` folder, or copy the individual folders you want into `~/.claude/`.

## Skills

Skills live in `skills/`.

- **android-clean-architecture** — Clean Architecture patterns for Android and Kotlin Multiplatform projects: module boundaries, dependency rules, UseCases, Repositories, and data-layer design with Room, SQLDelight, and Ktor.
- **batch-code-analysis-skill** — Orchestrates parallel code reviews by delegating batched analysis to `code-review-agent` workers. Triggers on requests like "review this PR" or "review these files". Not used for single-file reviews.
- **beautiful-mermaid** — Generates polished Mermaid diagrams (flowcharts, sequence, class, ER, state) via the `beautiful-mermaid` library with theming support and SVG or ASCII output.
- **caveman** — Ultra-compressed communication mode. Drops filler, articles, and pleasantries while keeping full technical accuracy. Cuts token usage roughly 75%.
- **customer-email** — Drafts plain-text customer-facing emails (release announcements, partner updates, support replies) and saves them to `~/Downloads` with a unique filename so prior drafts aren't overwritten.
- **diagnose** — Disciplined debug loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test.
- **jira** — Creates and manages Jira tickets via whichever Atlassian MCP server is available in the session (local Docker-backed or hosted). Targets `swankmp.atlassian.net`.

### Obsidian Skills (plugin)

Installed from the `obsidian-skills` marketplace plugin.

- **obsidian:defuddle** — Extracts clean markdown from web pages via the Defuddle CLI, stripping navigation/ads to save tokens. Use instead of `WebFetch` for standard pages (skip for URLs already ending in `.md`).
- **obsidian:json-canvas** — Creates and edits JSON Canvas files (`.canvas`) with nodes, edges, groups, and connections — mind maps, flowcharts, visual canvases.
- **obsidian:obsidian-bases** — Creates and edits Obsidian Bases (`.base` files): database-like views of notes with filters, formulas, and table/card views.
- **obsidian:obsidian-cli** — Drives a running Obsidian instance via the `obsidian` CLI to read, create, search, and manage notes; also supports plugin/theme development (reload, run JS, screenshots, DOM inspection).
- **obsidian:obsidian-markdown** — Authors valid Obsidian Flavored Markdown: wikilinks, embeds, callouts, frontmatter properties, tags, and comments.

## Statusline

`statusline.sh` renders a two-line status with model, directory, git branch, a colored context-usage bar, session cost, and elapsed time.

```
[Sonnet 4.6] 📁 my-repo | 🕊️ main
████░░░░░░ 42% | $0.18 | ⏱️ 3m 12s
```

The bar turns yellow at 70% context usage and red at 90%.

Wired up in `settings.json`:

```json
"statusLine": {
  "type": "command",
  "command": "~/.claude/statusline.sh"
}
```

Requires `jq`.

## Slash Commands

Custom commands live in `commands/`.

### `/arewedone`
Runs the `structural-completeness-reviewer` agent against recent changes to verify they're fully integrated, old code is removed, and no technical debt was introduced. Claude then immediately addresses the agent's findings.

### `/my-world`
Loads scoped context from my Obsidian dev-projects vault for the current repo — the matching project note, its one-hop dependencies, and (in full mode) related products, concepts, and a list of unprocessed raw sources. Backed by a JSON index that's auto-rebuilt when stale, with `grep` fallbacks if the index isn't available.

Pass `fast` to skip the broader cross-cutting passes when you just want quick orientation.

### `/wiki-lint`
Read-only structural health check for the same Obsidian vault. A single bash invocation runs all checks (broken links, asymmetric deps, missing frontmatter, orphans, unprocessed clippings, one-off tags) and prints a markdown report. Nothing is auto-fixed — you pick which findings to act on.

## Hooks

See [`hooks/README.md`](hooks/README.md) for the Windows clipboard-image-paste workaround.

The `Notification` hooks in `settings.json` also play sounds via `play-sound.sh` for permission prompts and idle prompts.
