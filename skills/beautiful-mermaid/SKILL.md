---
name: beautiful-mermaid
description: Best practices for creating Mermaid diagrams using the beautiful-mermaid library
metadata:
  tags: mermaid, diagrams, svg, ascii, flowchart, sequence, class, er, stateDiagram
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

## Rendering to SVG

When the user asks for an SVG file, use the render script bundled with this skill:

1. Write the mermaid diagram to a temporary `.mmd` file
2. Ensure `beautiful-mermaid` is installed: `npm ls beautiful-mermaid 2>/dev/null || npm install beautiful-mermaid`
3. Run: `node ~/.claude/skills/beautiful-mermaid/render-svg.mjs <input.mmd> <output.svg> [theme]`
4. Clean up the `.mmd` file after rendering

Available themes: `zinc-light`, `zinc-dark`, `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`, `catppuccin-mocha`, `catppuccin-latte`, `nord`, `nord-light`, `dracula`, `github-light`, `github-dark`, `solarized-light`, `solarized-dark`, `one-dark`

Example:
```bash
# Write diagram to temp file
cat <<'EOF' > /tmp/diagram.mmd
classDiagram
  class Foo {
    +bar() void
  }
EOF

# Ensure dependency is available
npm ls beautiful-mermaid 2>/dev/null || npm install beautiful-mermaid

# Render with optional theme
node ~/.claude/skills/beautiful-mermaid/render-svg.mjs /tmp/diagram.mmd docs/diagram.svg github-dark

# Clean up
rm /tmp/diagram.mmd
```
