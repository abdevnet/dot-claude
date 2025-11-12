---
name: Batch Code Analysis Skill
description: Analyzes large repositories by delegating batched reviews to Haiku 4.5 workers
---

# Batch Code Analysis Skill

You orchestrate large-scale code analysis with **Sonnet 4.5** by planning Haiku 4.5 subtasks, collecting their findings, and delivering a single concise report to the user.

## Instructions

### Role of Sonnet 4.5 (You)
- Interpret the user request (e.g., security scan, style audit, performance review, code review).
- Enumerate relevant files and split them into logical batches (≈10 files each).
- Launch a `Task` per batch using **Haiku 4.5**.
- Track completion status, retry failed batches when possible, and aggregate the structured outputs.
- Deduplicate overlapping issues and summarize the combined findings for the user.

### Role of Haiku 4.5 (Workers)
- Analyze the assigned file batch in isolation.
- Surface security, performance, style, or other requested issues with short explanations.
- Return JSON or Markdown that is easy to merge (avoid narrative text unless needed for clarity).

### Workflow
1. **Understand scope**: Confirm target repositories, directories, or file patterns.
2. **Plan batches**: Group files by feature, layer, or size. Keep batches small enough to fit Haiku 4.5’s context window.
3. **Dispatch tasks**: Create parallel Haiku 4.5 tasks (up to 10 concurrently) with clear instructions, including Code Review Skill guidance whenever performing a code review.
4. **Collect results**: Wait for all tasks, retry failures, and note missing files or partial results.
5. **Aggregate**: Merge JSON arrays, group by file/severity, and remove duplicates.
6. **Report**: Produce a structured summary with tables or bullet lists plus any remediation guidance.

## Task Schema

Use the following template (adjust `analysis_type`, `files`, or `output_format` as needed). When performing a code review, add the relevant standards excerpt from the Code Review Skill under `standards_context` so Haiku 4.5 evaluates each batch with the correct rules:

```json
{
  "task_name": "analyze_code_batch",
  "model": "haiku-4.5",
  "input": {
    "files": ["file1.py", "file2.py", "..."],
    "analysis_type": "security",
    "standards_context": "Summaries or sections pulled from the Code Review Skill when applicable"
  },
  "output_format": "json"
}
```

### Example Result

```json
{
  "batch_id": 3,
  "findings": [
    { "file": "auth.py", "issue": "Hardcoded secret key", "severity": "high" },
    { "file": "utils.py", "issue": "Input not sanitized", "severity": "medium" }
  ]
}
```

## Aggregation Guidance

After all batches finish:
1. Merge JSON findings from every batch.
2. Group entries by file and severity, keeping the highest severity per issue.
3. Flag missing or failed batches so the user knows where coverage is incomplete.
4. When the task is a code review, cite the specific standard or rule section provided by the Code Review Skill for every issue.
5. Generate a human-readable summary, for example:

| File | Issue | Severity |
|------|-------|----------|
| auth.py | Hardcoded secret key | High |
| utils.py | Input not sanitized | Medium |

**Formatting tip**: When presenting sections like “What’s Done Well,” output each ✅ item on its own line (or bullet) so the checklist remains readable.

## Optimization Guidelines
- Default batch size: 10 files; reduce if files are large or complex.
- Maximum parallel tasks: 10 to balance speed and resource limits.
- Always delegate analysis to Haiku 4.5 to preserve Sonnet 4.5’s context budget.
- Prefer JSON outputs for easy merging; only use Markdown if the user explicitly requests prose.
- Handle partial failures gracefully—surface completed findings and note pending work.

## Usage

Users might request:
- “Analyze this repository for potential security issues.”
- “Batch review the `/api` folder for performance problems.”
- “Scan only the recently changed files for style violations.”
- “Perform a code review of the latest backend changes against our standards.” (Load and embed the Code Review Skill guidance before dispatching batches.)

For each request, follow the workflow above, ensure Haiku 4.5 tasks reference the correct files, and return a single consolidated report.

## Notes
- Never attempt to analyze the entire repo directly; always break work into Haiku 4.5 batches.
- Keep Haiku 4.5 prompts focused to avoid long responses.
- For code review work, always run the Code Review Skill first and propagate its standards into each Haiku batch prompt.
- This skill is designed for Claude Code or Claude API orchestration environments where task delegation is available.
### Integrating the Code Review Skill
- When the user request is a code review, invoke the **Code Review Skill** to load the authoritative standards (C#, Angular, SQL Server) before dispatching Haiku batches.
- Include the relevant standards excerpts or references from the Code Review Skill output in every Haiku 4.5 batch prompt so each worker evaluates files against the same rules.
- If Haiku surfaces code review findings, map them back to the Code Review Skill sections (e.g., naming, documentation, SQL conventions) in the aggregated report.
- When non-code-review analysis is requested, you can skip this integration step.
