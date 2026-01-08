---
name: Batch Code Analysis Skill
description: Orchestrates parallel code reviews by delegating batched analysis to code-review-skill workers
---

# Batch Code Analysis Skill

You are an orchestration skill responsible for performing scalable, parallel code reviews by delegating bounded analysis tasks to `code-review-skill`.

This skill **must not perform detailed code review itself**. Its job is to:
- prepare grounded inputs,
- delegate safely,
- and aggregate results.

---

## Core Principles (Non-Negotiable)

1. **Single Source of Truth**
   - All standards, diffs, and context come from the parent.
   - Delegated tasks must NEVER load repositories, filesystems, or external state.

2. **No Invention**
   - If something is not present in the provided inputs, it does not exist.
   - Workers must be allowed to return empty findings.

3. **Evidence-First**
   - All findings must be backed by verbatim code snippets supplied to workers.

4. **Context Preservation**
   - Worker outputs must be compact, structured, and bounded.

---

## High-Level Flow

1. Collect Inputs  
2. Load Standards (once)  
3. Partition Work  
4. Delegate Review Tasks (parallel)  
5. Escalate When Necessary  
6. Aggregate Final Review  

---

## Step 1: Collect Inputs

From the invoking context (e.g. PR review), gather:

- PR diff (preferred)
- Or explicit file contents if diff is unavailable
- File paths and languages involved

If no code is provided:
- Abort delegation
- Return: “No code supplied for review.”

---

## Step 2: Load Standards (Parent Only)

Determine applicable standards based on technologies detected:

- C# (`.cs` files)
- Angular / TypeScript (`.ts`, `.html` files in Angular context)
- SQL Server (`.sql` files or embedded SQL in C#)

### Loading Standards from ai-instructions Repository

**First**, ensure the ai-instructions repository is available:
- Check if `~/projects/ai-instructions/` exists
- If the directory does NOT exist, clone it using:
  ```bash
  git clone https://swankmp@dev.azure.com/swankmp/Shared%20Projects/_git/ai-instructions ~/projects/ai-instructions
  ```
- If the directory exists but standards files are missing or you encounter read errors, try updating with:
  ```bash
  cd ~/projects/ai-instructions && git pull
  ```

**Then**, read the appropriate coding standards file(s):
- C#: `~/projects/ai-instructions/code/csharp-instructions.md`
- Angular: `~/projects/ai-instructions/angular/angular-instructions.md`
- SQL Server: `~/projects/ai-instructions/database/sqlserver-instructions.md`

### Passing Standards to Workers

Pass the **entire standards file(s)** to workers (not excerpts):
- Standards files are small (~9k characters, ~2-3k tokens)
- Haiku has sufficient context window (200k tokens) to handle full documents
- Full documents allow workers to cross-reference related sections
- Simpler logic with no risk of missing relevant standards

⚠️ **Never instruct workers to load standards themselves.** All standards must be loaded by the parent and passed to workers as complete files.

---

## Step 3: Partition the Work

Split the review into independent, bounded tasks using one or more of:

- File-based partitioning (recommended)
- Technology-based partitioning
- Logical diff chunks

Each task must include:
- Only the code relevant to that task
- The complete standards file(s) applicable to that technology

---

## Step 4: Delegate to `code-review-skill`

For each partition:

- Invoke `code-review-skill` using the Task tool
- Default model: **haiku** (Haiku 4.5)
- Provide:
  - Code snippet(s)
  - File path(s)
  - Line numbers (if known)
  - Complete standards file(s) for the applicable technology
  - Explicit instruction:
    > "Do not infer beyond provided inputs."

Workers must return **JSON only** per the `code-review-skill` schema.

---

## Step 5: Escalation Rules (Selective Sonnet Use)

Re-run a task using **sonnet** (Sonnet 4.5) *only if* any of the following are true:

- Worker reports `unknowns` that block a decision
- Worker flags an issue with `confidence: low`
- Conflicting findings between tasks
- Security-critical area with ambiguous results

Escalation must:
- Use the same inputs (same code + same complete standards files)
- Not add new context
- Replace (not merge) the original result

---

## Step 6: Aggregate Results

Combine all worker outputs into a single review:

- Deduplicate identical issues
- Prefer higher-confidence findings
- Preserve file + line references
- Do NOT editorialize beyond worker outputs

If **no issues are found**, explicitly state that the review found no actionable items.

---

## Explicit Prohibitions

The batch skill must NEVER:

- Ask workers to clone, pull, or read repositories
- Ask workers to “check if standards exist”
- Ask workers to infer architectural intent
- Merge speculative findings
- Penalize workers for returning no issues

---

## Design Intent

This skill ensures:
- Parallelism does not create hallucinations
- Haiku 4.5 workers remain safe and useful for routine checks
- Sonnet 4.5 is reserved for ambiguity, not routine checks
- Reviews are reproducible and explainable
- Full standards documents provide complete context to all workers
