# API Reference

## Installation

```bash
npm install beautiful-mermaid
# or
bun add beautiful-mermaid
```

## `renderMermaid(text, options?): Promise<string>`

Renders Mermaid source to an SVG string. Auto-detects diagram type from the first line.

```typescript
import { renderMermaid } from 'beautiful-mermaid';

const svg = await renderMermaid(`
  graph TD
    A[Start] --> B[End]
`);
```

### RenderOptions

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `bg` | `string` | `'#FFFFFF'` | Background color |
| `fg` | `string` | `'#27272A'` | Foreground/text color |
| `line` | `string?` | derived | Edge/connector color |
| `accent` | `string?` | derived | Arrow heads, highlights |
| `muted` | `string?` | derived | Secondary text, edge labels |
| `surface` | `string?` | derived | Node fill tint |
| `border` | `string?` | derived | Node/group stroke |
| `font` | `string` | `'Inter'` | Font family |
| `padding` | `number` | `40` | Canvas padding (px) |
| `nodeSpacing` | `number` | `24` | Horizontal spacing between sibling nodes |
| `layerSpacing` | `number` | `40` | Vertical spacing between layers |
| `transparent` | `boolean` | `false` | Transparent background |

## `renderMermaidAscii(text, options?): string`

Synchronous. Renders to ASCII or Unicode box-drawing characters. Useful for terminal output.

```typescript
import { renderMermaidAscii } from 'beautiful-mermaid';

const ascii = renderMermaidAscii(`
  graph LR
    A --> B --> C
`);
console.log(ascii);
```

### AsciiRenderOptions

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `useAscii` | `boolean` | `false` | `true` = pure ASCII, `false` = Unicode box-drawing |
| `paddingX` | `number` | `5` | Horizontal spacing between nodes |
| `paddingY` | `number` | `5` | Vertical spacing between nodes |
| `boxBorderPadding` | `number` | `1` | Padding inside node boxes |

## `THEMES: Record<string, DiagramColors>`

Object with 15 built-in theme presets. See [theming.md](theming.md).

## `DEFAULTS`

```typescript
{ bg: '#FFFFFF', fg: '#27272A' }
```

## `fromShikiTheme(theme): DiagramColors`

Extracts diagram colors from any Shiki/VS Code theme. See [theming.md](theming.md).

## `parseMermaid(text): MermaidGraph`

Exported parser for the intermediate graph representation. Useful for custom rendering or analysis.

## Browser / CDN Usage

```html
<script src="https://unpkg.com/beautiful-mermaid/dist/beautiful-mermaid.browser.global.js"></script>
<script>
  const { renderMermaid, THEMES } = beautifulMermaid;

  renderMermaid('graph TD\n  A --> B', THEMES['dracula'])
    .then(svg => {
      document.getElementById('diagram').innerHTML = svg;
    });
</script>
```

Also available via jsDelivr:
```html
<script src="https://cdn.jsdelivr.net/npm/beautiful-mermaid/dist/beautiful-mermaid.browser.global.js"></script>
```
