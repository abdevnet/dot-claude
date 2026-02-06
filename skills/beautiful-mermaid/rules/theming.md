# Theming

## Two-Color Foundation (Mono Mode)

Provide just `bg` and `fg`. All other colors are derived automatically via `color-mix()`:

| Element | Derivation (fg mixed into bg) |
|---------|------|
| Primary text | 100% fg |
| Secondary text | 60% fg |
| Muted text / edge labels | 40% fg |
| Faint text | 25% fg |
| Edge lines | 30% fg |
| Arrow heads | 50% fg |
| Node fill | 3% fg |
| Node stroke | 20% fg |
| Group header | 5% fg |
| Inner dividers | 12% fg |

```typescript
import { renderMermaid } from 'beautiful-mermaid';

const svg = await renderMermaid(diagram, {
  bg: '#1a1b26',
  fg: '#c0caf5'
});
```

## Enriched Mode

Override any derived color explicitly:

```typescript
const svg = await renderMermaid(diagram, {
  bg: '#FFFFFF',
  fg: '#27272A',
  line: '#a0a0a0',
  accent: '#3b82f6',
  muted: '#6b7280',
  surface: '#f3f4f6',
  border: '#d1d5db'
});
```

| Property | Role |
|----------|------|
| `line` | Edge/connector color |
| `accent` | Arrow heads, highlights |
| `muted` | Secondary text, edge labels |
| `surface` | Node fill tint |
| `border` | Node/group stroke |

## 15 Built-in Themes

Access via `THEMES`:

```typescript
import { renderMermaid, THEMES } from 'beautiful-mermaid';
const svg = await renderMermaid(diagram, THEMES['tokyo-night']);
```

Available themes:
- `zinc-light`, `zinc-dark`
- `tokyo-night`, `tokyo-night-storm`, `tokyo-night-light`
- `catppuccin-mocha`, `catppuccin-latte`
- `nord`, `nord-light`
- `dracula`
- `github-light`, `github-dark`
- `solarized-light`, `solarized-dark`
- `one-dark`

## Shiki / VS Code Theme Integration

Convert any Shiki theme into diagram colors:

```typescript
import { fromShikiTheme } from 'beautiful-mermaid';
import { createHighlighter } from 'shiki';

const highlighter = await createHighlighter({ themes: ['vitesse-dark'] });
const theme = highlighter.getTheme('vitesse-dark');
const colors = fromShikiTheme(theme);
const svg = await renderMermaid(diagram, colors);
```

## Runtime Theme Switching

All colors are CSS custom properties on the `<svg>`. Switch themes without re-rendering:

```javascript
const svgEl = document.querySelector('svg');
svgEl.style.setProperty('--bg', '#282a36');
svgEl.style.setProperty('--fg', '#f8f8f2');
```

## Transparent Background

```typescript
const svg = await renderMermaid(diagram, { transparent: true });
```

## Font

Default font is `Inter`. Class and ER diagrams use `JetBrains Mono` for member text.

```typescript
const svg = await renderMermaid(diagram, { font: 'Fira Code' });
```
