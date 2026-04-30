---
name: beautiful-mermaid
description: Creates polished, professional Mermaid diagrams using the beautiful-mermaid rendering library with advanced theming support. Use when user asks to create a diagram, make a flowchart, draw a sequence diagram, visualize a class hierarchy, create an ER diagram, make a state diagram, or any request involving Mermaid syntax, .mermaid files, or visual representations of workflows, architectures, and relationships. Supports flowcharts, state diagrams, sequence diagrams, class diagrams, and ER diagrams with built-in themes, CSS variable customization, and both SVG and ASCII output via the renderMermaid API.
metadata:
  tags: [mermaid, diagrams, svg, ascii, flowchart, sequence, class, er, state-diagram, theming]
  version: 1.0.0
---

## When to use

Use this skill whenever the user asks you to create, generate, or render a Mermaid diagram. This skill provides the correct syntax, theming options, and API usage for the `beautiful-mermaid` library — a TypeScript library that renders Mermaid syntax into SVG or ASCII/Unicode text art.

## How to use

Read individual rule files for detailed syntax, examples, and configuration:

- [rules/flowchart.md](rules/flowchart.md) - Flowcharts and state diagrams: node shapes, edge types, subgraphs, directions
- [rules/sequence.md](rules/sequence.md) - Sequence diagrams: participants, actors, messages, blocks, notes
- [rules/class.md](rules/class.md) - Class diagrams: attributes, methods, visibility, relationships, namespaces
- [rules/er.md](rules/er.md) - ER diagrams: entities, attributes, crow's foot cardinality, key constraints
- [rules/theming.md](rules/theming.md) - Theming: built-in themes, two-color derivation, CSS variables, Shiki integration
- [rules/api.md](rules/api.md) - API reference: renderMermaid, renderMermaidAscii, options, browser usage

## General Guidelines

1. **Pick the right diagram type** for what the user is describing:
   - Architecture / data flow / decision trees → `graph` or `flowchart`
   - Request/response sequences between systems → `sequenceDiagram`
   - Object-oriented design → `classDiagram`
   - Database schema → `erDiagram`
   - Lifecycle / state machines → `stateDiagram-v2`

2. **Keep diagrams readable**: avoid more than ~15 nodes in a single diagram. Split into multiple diagrams if needed.

3. **Use meaningful node IDs and labels**: `auth[Authentication Service]` is better than `A[Authentication Service]`.

4. **Choose direction wisely**: `TD` (top-down) for hierarchies, `LR` (left-right) for sequential flows.

5. **Use subgraphs** to group related nodes visually.

6. **Output the raw Mermaid text** in a fenced code block tagged `mermaid` so the user can copy and render it.

7. **Keep labels to a single short line.** This renderer ignores `<br/>`, `<br>`, `\n`, and literal newlines — they render as visible characters. See [rules/flowchart.md](rules/flowchart.md#labels-and-line-breaks) for the workaround (split across connected nodes; avoid quoted labels unless needed for parser-breaking characters).

## Picking the right output

**Default to SVG.** Render the SVG, show the user the file path, and stop there. SVG renders in a single subprocess (~1s); PNG adds Chrome headless on top, takes 5–8s, and needs sandbox-disabled execution on macOS — every PNG is a noticeable delay. Most uses (Confluence, README embeds, viewing in an editor, sharing as a file) work directly off the SVG.

**Only render PNG when the user explicitly asks** (e.g. "give me a PNG", "I need to paste this into Slack/Teams/email", "make me an image"). If you've already rendered the SVG and the user might want a PNG, ask: *"Want me to also render a PNG?"* — don't speculatively render both.

| Goal | Use this |
|------|----------|
| Quick structural check while iterating | `renderMermaidAscii` (instant, terminal-friendly) |
| Default deliverable — embedding, sharing, viewing | SVG via `render-svg.mjs` |
| User explicitly asked for an image file | PNG via `render-png.mjs` (after asking, if intent is unclear) |

For ASCII, write a tiny one-off node script — there's no bundled CLI for it. Useful when you're not sure the structure is right and don't want to pay for a screenshot round-trip.

## Rendering to SVG or PNG

Both bundled scripts assume `beautiful-mermaid` is on the user's `node_modules` path. Check once per session:

```bash
npm ls beautiful-mermaid 2>/dev/null || npm install beautiful-mermaid
```

### SVG

```bash
node ~/.claude/skills/beautiful-mermaid/render-svg.mjs <input.mmd> <output.svg> [theme]
```

### PNG (one-shot)

`render-png.mjs` does the full pipeline: SVG render → HTML wrapper with the right background → Chrome headless screenshot → cleanup. Window size auto-fits the SVG's intrinsic dimensions, so you don't have to guess.

```bash
node ~/.claude/skills/beautiful-mermaid/render-png.mjs <input.mmd> <output.png> [theme] [width] [height]
```

`width`/`height` are optional overrides; omit them to use the SVG's native size + 40px padding.

### Chrome headless gotchas (macOS)

Two issues you'll hit on a default macOS Claude Code setup:

- **Sandbox blocks Chrome's profile and crashpad directories.** You'll see `open ~/Library/Application Support/Google/Chrome/Crashpad/...: Operation not permitted` and the screenshot won't be written. Re-run the Bash tool call with `dangerouslyDisableSandbox: true`. (`render-png.mjs` always uses a fresh `--user-data-dir` under `$TMPDIR`, but Chrome still touches `~/Library/...` for crashpad.)
- **Concurrent Chrome runs collide on the default profile dir.** `render-png.mjs` mints a unique profile per invocation, so back-to-back renders don't conflict.

If you call Chrome by hand instead of using `render-png.mjs`, do both yourself: pass `--user-data-dir=$(mktemp -d)` and run with sandbox off.

Available themes: `zinc-light`, `zinc-dark`, `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `nord-light`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`

Example end-to-end:
```bash
cat <<'EOF' > /tmp/diagram.mmd
classDiagram
  class Foo {
    +bar() void
  }
EOF
npm ls beautiful-mermaid 2>/dev/null || npm install beautiful-mermaid
node ~/.claude/skills/beautiful-mermaid/render-png.mjs /tmp/diagram.mmd docs/diagram.png github-dark
rm /tmp/diagram.mmd
```

### Theme background colors (reference)

`render-png.mjs` resolves these automatically. Listed here for cases where you're hand-rolling the wrapper or need to match a different surface.

| Theme | Background |
|-------|-----------|
| `github-dark` | `#0d1117` |
| `github-light` | `#ffffff` |
| `tokyo-night` | `#1a1b26` |
| `tokyo-night-storm` | `#24283b` |
| `tokyo-night-light` | `#d5d6db` |
| `catppuccin-mocha` | `#1e1e2e` |
| `catppuccin-latte` | `#eff1f5` |
| `dracula` | `#282a36` |
| `nord` | `#2e3440` |
| `nord-light` | `#eceff4` |
| `solarized-dark` | `#002b36` |
| `solarized-light` | `#fdf6e3` |
| `one-dark` | `#282c34` |
| `zinc-dark` | `#09090b` |
| `zinc-light` | `#ffffff` |
