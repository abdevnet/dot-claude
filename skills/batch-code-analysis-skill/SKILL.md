---
name: batch-code-analysis-skill
description: >
  Orchestrates parallel code reviews by delegating batched analysis to
  code-review-agent workers. Use when reviewing multiple files, a PR diff,
  or any multi-file code change against team coding standards (C#, Angular,
  TypeScript, SQL Server). Triggers on requests like "review this PR",
  "review these files", or "batch code review". Do NOT use for single-file reviews.
---

# Batch Code Analysis Skill

Orchestration skill for scalable, parallel code reviews. Delegates bounded analysis tasks to `code-review-agent` — never performs detailed review itself.

Responsibilities: prepare grounded inputs, delegate safely, aggregate results.

---

## Core Principles

1. **Single Source of Truth** — All standards, diffs, and context come from the parent. Workers must NEVER load repositories, filesystems, or external state.
2. **No Invention** — If something is not in the provided inputs, it does not exist. Workers may return empty findings.
3. **Evidence-First** — All findings must be backed by verbatim code snippets supplied to workers.
4. **Context Preservation** — Worker outputs must be compact, structured, and bounded.

---

## Workflow

### Step 1: Collect Inputs

From the invoking context (e.g. PR review), gather:
- PR diff (preferred) or explicit file contents
- File paths and languages involved

If no code is provided, abort and return: "No code supplied for review."

### Step 2: Load Standards

Standards are bundled in `references/standards/`. Determine applicable files based on detected technologies:
- C# (`.cs`): `references/standards/csharp-instructions.md`
- Angular/TypeScript (`.ts`, `.html`): `references/standards/angular-instructions.md`
- SQL Server (`.sql` or embedded SQL): `references/standards/sqlserver-instructions.md`

For embedded SQL detection in C#/Java files, see [references/embedded-sql-detection.md](references/embedded-sql-detection.md).

Pass the **entire standards file(s)** to workers (not excerpts). Standards files are small (~2-3k tokens) and Haiku has sufficient context. Never instruct workers to load standards themselves.

### Step 3: Partition Work

Split the review into independent, bounded tasks using:
- File-based partitioning (recommended)
- Technology-based partitioning
- Logical diff chunks

**Partition sizing:**
- Target 1-3 files per worker task
- Keep each partition under ~2,000 lines of diff
- Group related files (e.g., a service + its interface) into the same partition
- Never split a single file across partitions

Each task must include only the code relevant to that task plus the complete applicable standards file(s).

### Step 4: Delegate to `code-review-agent`

For each partition, invoke `code-review-agent` using the Task tool:
- Default model: **haiku** (Haiku 4.5)
- Provide: code snippet(s), file path(s), line numbers (if known), complete standards file(s)
- Include instruction: "Do not infer beyond provided inputs."

Workers return JSON per the `code-review-agent` schema.

### Step 5: Escalation (Selective Sonnet Use)

Re-run a task using **sonnet** (Sonnet 4.5) only if:
- Worker reports `unknowns` that block a decision
- Worker flags an issue with `confidence: low`
- Conflicting findings between tasks
- Security-critical area with ambiguous results

Escalation rules:
- Use the same inputs (same code + same standards)
- Do not add new context
- Replace (not merge) the original result

### Step 6: Worker Failure Handling

- If a worker returns malformed output, retry once with the same inputs
- If retry fails, escalate that partition to Sonnet
- If a worker times out, include the partition in the final report as "unreviewed"
- Never silently drop a partition

### Step 7: Aggregate Results

Combine all worker outputs into a single review:
- Deduplicate identical issues
- Prefer higher-confidence findings
- Preserve file + line references
- Do NOT editorialize beyond worker outputs

If no issues are found, explicitly state the review found no actionable items.

### Step 8: Final Output Format

Present the aggregated review as a structured markdown report:

```markdown
## Code Review Summary

**Verdict:** approve | comment | request_changes
**Files reviewed:** N | **Partitions:** N | **Escalations:** N

### Critical Issues
- **[Title]** — `file:lines` — description + suggested fix

### Standard Violations
- **[Title]** — `file:lines` — standard ref + description

### Suggestions
- **[Title]** — `file:lines` — description

### Positive Notes
- Bullet points

### Unreviewed (if any)
- Partitions that failed or timed out
```

For execution metrics, see [references/metrics.md](references/metrics.md). Append a `_metrics` JSON block after the markdown report.

---

## Prohibitions

The batch skill must NEVER:
- Ask workers to clone, pull, or read repositories
- Ask workers to "check if standards exist"
- Ask workers to infer architectural intent
- Merge speculative findings
- Penalize workers for returning no issues
