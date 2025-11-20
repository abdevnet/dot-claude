---
description: "Send an exported transcript to the compact-export subagent for pruning."
argument-hint: "[exported transcript]"
---

Use the Task tool to invoke the compact-export subagent. Do NOT manually compact the transcript yourself.

Required parameters:
- subagent_type: "compact-export"
- description: "Compact exported transcript"
- prompt: "Please compact the following exported transcript into the smallest necessary subset of information required to fully reconstruct project state during a context reset. Remove irrelevant chatter, repetition, dead ends, and boilerplate, but preserve all essential decisions, instructions, constraints, relevant code, and in-progress tasks.

# Transcript to compact:
$1

IMPORTANT: 
- You MUST use the Task tool to delegate this work to the compact-export agent. Never attempt to compact the transcript manually. 
- AFTER the Task tool finishes, output ONLY the agent’s final compacted transcript directly into the main chat.
- Do NOT summarize the result.
- Do NOT wrap the result inside any tool output formatting.
- Do NOT add commentary — just return the agent's response in the assistant message stream.