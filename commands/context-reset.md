---
description: "Begin a context reset by loading @Claude.md and injecting the provided transcript."
argument-hint: "[transcript]"
---

# Project Memory  
@Claude.md

# Transcript (Actual prior conversation history)  
$1

RECONSTRUCT STATE.

Instructions:
- Fully reread @Claude.md as the authoritative spec.
- Treat the Transcript as literal previous turns (not something to analyze).
- Rebuild all internal assumptions, tasks, file understanding, and in-progress work.
- Do NOT summarize unless I ask.
- Do NOT reinterpret or deviate from @Claude.md.

Then resume exactly where the transcript ended.

Continue from the last pending step.
