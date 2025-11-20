---
description: "Display the full context-reset workflow checklist, including export, compaction, clearing, and reinjection."
---

# 🧹 Context Reset Checklist

Follow these steps to safely reset context while preserving project memory and minimizing token usage.
---
## ✅ 1. Prepare for reset  
Run: /context-prepare-reset
---
## ✅ 2. Export the transcript  
Run: /export
Copy the relevant section of the export.
---
## ✅ 3. Compact the exported transcript  (optional)
Run: /context-compact [paste exported transcript here]
Copy the compacted output.
---
## ✅ 4. Clear the conversation  
Run: /clear
This wipes context but keeps slash commands and agents.
---
## ✅ 5. Reinject the compacted transcript  
Run: /context-reset [paste compacted transcript here]
This restores project state using @Claude.md plus your compact transcript.
---
## ✅ 6. Resume work  
Once Claude finishes reconstructing state, run: Continue.
---
# 👍 You're ready to proceed!
Use this checklist anytime to ensure you follow the optimal, clean context-reset workflow.