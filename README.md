A collection of skills, agents, commands, hooks, and a statusline for Claude Code.

To use, clone this repo into your local `.claude` folder, or copy the individual folders you want into `~/.claude/`.

## Skills & Agents

The main skills I use are the code-review-skill along with the batch-code-analysis-skill.

After updating your local `.claude` folder, start Claude Code in the terminal inside your code repo and ask Claude to do a code review.

There are known issues where Claude doesn't always invoke the skill that it should. I put this line in my main `Claude.MD` file to make sure the skills activate. Some developers use hooks to accomplish this.

```
Always use the batch-code-analysis-skill to break the work up into tasks running in parallel when asked to do a code review.
Each task should use the code-review-skill.
```

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
