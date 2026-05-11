---
name: html-brainstorm
description: Produce single-file HTML artifacts for design exploration, architecture brainstorming, and throwaway interactive prototypes — instead of markdown plans that won't get read. Use whenever the user wants to explore design directions, fan out approaches side-by-side, sketch a system architecture, mock up a UI, prototype an animation or interaction, build a throwaway editor with an export-to-prompt button, or says "brainstorm", "explore options", "show me a few designs", "diagram this", "mock this up", "prototype this idea", "compare approaches" — even when they don't explicitly say "HTML". Default to this skill any time the artifact would be more useful as something openable in a browser than as prose.
---

# HTML Brainstorm

Markdown is fine for short answers and capture. Once an exploration grows past ~100 lines or starts trying to convey colour, layout, motion, or system structure, markdown stops working — people skim it, then stop reading. **HTML artifacts solve that.** A single self-contained `.html` file can carry tables, SVG, embedded CSS, inline JS, and interactive controls; it opens in any browser and can be linked or attached without conversion.

Use this skill to produce HTML artifacts that anchor a design / architecture / prototype conversation. The artifact is the *medium*, not the deliverable — once a direction is picked, the codified version goes into the real codebase.

## When this skill applies vs. siblings

- **This skill** — pre-decision exploration. The output is a standalone HTML file in `/tmp` or a workspace folder. Goal: help the user see options, react to them, and pick one. No project integration.
- **`prototype` skill** — once the question is narrower and the answer needs to live near the real code (a runnable terminal app for logic, or UI variants on a real route).
- **`frontend-design`** — once a single design direction is chosen and it's time to produce production-quality components.

If the user is still in "I'm not sure what I want yet" territory, this skill is the right call. If they've picked a direction and want it implemented, hand off.

## Three modes

Pick the mode from the user's prompt. If it's ambiguous, ask one clarifying question — getting this wrong wastes the whole artifact.

### Mode 1 — Design fan-out

The user wants to compare directions. Their prompt sounds like:
- "I'm not sure what direction to take X — give me a few options"
- "Show me 3-6 different ways to lay out this dashboard"
- "Compare a Stripe-style vs. Linear-style vs. Notion-style for this landing page"

**Output shape.** A single HTML file with N variations rendered live in a grid (or stacked sections with a top nav). Each variation is labelled with the trade-off it's making — *information density*, *visual weight*, *novelty vs. familiarity*. The user reads the trade-off labels first, then looks at the variation, then says "this one — but with the colour from #2."

**Patterns that work:**
- Use real placeholder content, not Lorem ipsum. Generic content makes options look identical.
- Vary the dimensions you're trying to test, hold others constant. If the question is layout, keep colour/typography consistent across variants. If the question is brand tone, hold layout constant.
- 3-6 variations. Fewer than 3 is just a comparison. More than 6 is overwhelming and stops being useful.
- Put the trade-off label *above* the variation, not buried in caption text.
- Anchor with a `DESIGN.md` if one exists for the brand the user is targeting (see [[awesome-design-md-pre-paywall]] in their vault for examples). Without an aesthetic anchor, output trends generic.

### Mode 2 — Architecture brainstorm

The user wants to think out loud about a system. Their prompt sounds like:
- "Help me think through how this service should be structured"
- "What does the data flow look like for X?"
- "Diagram the request path through these three services"
- "Sketch a few different ways we could split this monolith"

**Output shape.** A single HTML file with inline SVG diagrams. Boxes-and-arrows for component maps, swimlanes for sequenced flows, a flowchart for decision logic. Include short prose under each diagram explaining what it shows and what trade-off it represents.

**Patterns that work:**
- Use SVG, not ASCII art. ASCII flattens spatial relationships that are the whole point of a diagram.
- For "compare architectures" prompts, render 2-3 alternatives side-by-side with a *trade-off table* underneath: latency, complexity, blast-radius, cost, etc. The table is what the user actually reads.
- For "trace the path" prompts, use a swimlane (one row per service/actor) and number the steps. Clickable steps that highlight the corresponding code snippet are a force-multiplier when the source is in a known repo.
- Annotate the *risky* parts inline — failure modes, retry behaviour, where state crosses boundaries. The diagram is most useful when it surfaces the things that aren't obvious from reading code.
- For data flow, distinguish synchronous calls from async/queued ones visually (solid vs. dashed arrows is the standard).

### Mode 3 — Throwaway interactive editor

The user wants to *feel* something — an animation, a parameter sweep, a tuning loop. Their prompt sounds like:
- "Let me play with this easing curve before we wire it in"
- "I need to reorder/triage these N items — give me a UI for it"
- "Build me a prompt tuner with a side-by-side preview"
- "Let me see what this looks like at different breakpoints"

**Output shape.** A single HTML file with controls (sliders, knobs, drag-and-drop, dropdowns) wired to a live preview. **Always end with an export button** — "copy as JSON", "copy as prompt", "copy diff", "copy markdown" — that turns whatever the user did in the UI back into something pasteable into the next Claude conversation. Without the export button, the loop doesn't close and the artifact is wasted.

**Patterns that work:**
- Pre-fill the editor with the agent's best guess so the user can react to it instead of starting from a blank state.
- Show the underlying values alongside the visual — a slider plus the literal `cubic-bezier(.42, 0, .58, 1)` it's currently set to. The literal value is what gets pasted back.
- For triage / reorder UIs, use HTML5 drag-and-drop (or click-to-cycle through buckets). Persist nothing — state is in memory, gone on refresh, that's fine.
- For prompt tuners, render the filled-in template live next to the editable template. Highlight variable slots so the user knows what's substituted.

## Workflow

1. **Decide the mode.** Read the user's prompt. If ambiguous between modes 1/2/3, ask one targeted question. ("Are you trying to compare a few visual directions, or thinking through how the system fits together?")
2. **Decide the trade-off axis.** What is the user actually trying to choose between? Layout vs. tone? Two-service vs. three-service split? Easing curve shape? The variation across the artifact should be that axis; everything else stays constant.
3. **Write to a single self-contained `.html` file.** No external CSS, no external JS, no build step. Inline everything. Default location: `/tmp/<descriptive-name>.html` unless the user specifies otherwise.
4. **Tell the user where it is and how to open it.** `open /tmp/foo.html` on macOS opens the default browser. State the path explicitly so they can re-open or share it.
5. **Iterate by editing the file in place.** When the user says "more like #2 but bolder typography", edit and tell them to refresh. Don't generate a second file unless the variation is large enough that side-by-side comparison helps.
6. **Capture the decision separately.** When a direction is picked, the artifact has done its job. The actual decision (chosen variant + reasoning) belongs in a commit message, ADR, ticket, or a short note — *not* the HTML file. The HTML is throwaway.

## Caveats

- **HTML generation is 2-4× slower than markdown.** That cost is paid once; the savings come from the artifact actually getting read and decided on. Worth it for exploration; overkill for a one-line answer.
- **Diffs are noisy.** Don't check these into the project repo. They live in `/tmp` or a scratch folder; the *decision* is what gets committed.
- **Don't pre-skill it into a single template.** Each brainstorm is shaped by its question. A reusable template across modes will produce generic output. Prompt from scratch each time, even if you've done a similar artifact before.
- **Anchor aesthetics or accept the slop.** Without a `DESIGN.md` or explicit reference site, output drifts toward generic AI styling (purple gradients, Inter, three rounded cards). Either provide an anchor up front or accept the output is for ideating shape, not look.

## Quick template — single-file HTML scaffold

When you don't have a more specific structure in mind, this scaffold works for all three modes:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{{ Brainstorm title }}</title>
  <style>
    :root { --bg: #0b0d10; --fg: #e6e8ec; --muted: #8a929c; --accent: #6ee7b7; --line: #1f242c; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
    main { max-width: 1200px; margin: 0 auto; padding: 32px; }
    h1 { font-size: 22px; margin: 0 0 4px; }
    .lede { color: var(--muted); margin: 0 0 32px; }
    .grid { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
    .card { border: 1px solid var(--line); border-radius: 12px; padding: 20px; background: #11151a; }
    .tradeoff { color: var(--accent); font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 8px; }
    .card h2 { font-size: 17px; margin: 0 0 12px; }
    .controls { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; padding: 16px 0; border-top: 1px solid var(--line); margin-top: 24px; }
    button { background: var(--accent); color: #0b0d10; border: 0; padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; }
    button.ghost { background: transparent; color: var(--fg); border: 1px solid var(--line); }
    code { background: #1a1f26; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
  </style>
</head>
<body>
  <main>
    <h1>{{ Title }}</h1>
    <p class="lede">{{ One-line framing of what's being explored and what to look for. }}</p>

    <section class="grid">
      <article class="card">
        <p class="tradeoff">{{ Trade-off this option makes }}</p>
        <h2>{{ Option name }}</h2>
        {{ Variation content — mockup, diagram, controls }}
      </article>
      <!-- repeat for each variation -->
    </section>

    <!-- For Mode 3 (interactive editor), include a controls bar with an export button: -->
    <div class="controls">
      <button onclick="copyExport()">Copy as prompt</button>
      <button class="ghost" onclick="location.reload()">Reset</button>
      <span id="status" style="color: var(--muted)"></span>
    </div>
  </main>
  <script>
    function copyExport() {
      const payload = JSON.stringify(/* current state */ {}, null, 2);
      navigator.clipboard.writeText(payload).then(() => {
        document.getElementById('status').textContent = 'Copied — paste into Claude.';
      });
    }
  </script>
</body>
</html>
```

The scaffold is a starting point, not a constraint — adapt the structure to fit the artifact. A swimlane diagram doesn't want a card grid; an animation tuner doesn't want trade-off labels. Keep the spirit (single file, self-contained, dark by default, export button when interactive) and let the rest follow the question.
