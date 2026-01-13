---
name: Batch Code Analysis Skill
description: Orchestrates parallel code reviews by delegating batched analysis to code-review-agent workers
---

# Batch Code Analysis Skill

You are an orchestration skill responsible for performing scalable, parallel code reviews by delegating bounded analysis tasks to `code-review-agent`.

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

Detecting Embedded SQL in Repository Code

  When reviewing repository/data access layer code (e.g., files with "Repository", "DataAccess", "Dal" in the path or name), check for embedded SQL queries even if the primary language is C#/Java/etc.

  Indicators of embedded SQL:
  - String literals containing SQL keywords: SELECT, INSERT, UPDATE, DELETE, FROM, WHERE
  - ORM/data access patterns:
    - Dapper: connection.QueryAsync<T>("SELECT ..."), connection.ExecuteAsync("INSERT ...")
    - ADO.NET: SqlCommand, cmd.CommandText = "SELECT ..."
    - Entity Framework raw SQL: FromSqlRaw(), ExecuteSqlRaw()
    - JDBC: executeQuery("SELECT ..."), executeUpdate("INSERT ...")

  Action required:
  If embedded SQL is detected, load both the primary language standards (C#, Java, etc.) and SQL Server standards, then pass both to workers.

  Example:
  // Detected: DeviceRegistrationRepository.cs contains:
  private static string GetCustomerSql()
  {
      return @"SELECT [Id], [Name] FROM [dbo].[Customer] WHERE [Id] = @CustomerId";
  }


  Workers should review:
  - C# aspects: method naming, string formatting, parameterization usage
  - SQL aspects: schema prefixes, parameterization, column naming, data types

  ⚠️ Do not skip SQL standards even if SQL is "just strings" in the code - query quality, injection protection, and standards adherence are critical.


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

## Step 4: Delegate to `code-review-agent`

For each partition:

- Invoke `code-review-agent` using the Task tool
- Default model: **haiku** (Haiku 4.5)
- Provide:
  - Code snippet(s)
  - File path(s)
  - Line numbers (if known)
  - Complete standards file(s) for the applicable technology
  - Explicit instruction:
    > "Do not infer beyond provided inputs."

Workers must return **JSON only** per the `code-review-agent` schema.

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

## Step 7: Metrics Collection

After aggregation, collect and output execution metrics to enable cost analysis and optimization.

### Metrics to Track

During orchestration, maintain counters for:

**Worker Invocations**
- `haiku_invocations`: Number of tasks sent to Haiku
- `sonnet_invocations`: Number of tasks sent to Sonnet (escalations only)
- `total_invocations`: Sum of all worker calls

**Escalation Tracking**
- `escalation_count`: Number of Haiku → Sonnet escalations
- `escalation_reasons`: List of why each escalation occurred (unknowns, low_confidence, conflicts, security_ambiguity)

**Workload Distribution**
- `files_reviewed`: Total files processed
- `partitions_created`: Number of work partitions
- `files_per_partition_avg`: Average files per worker task

**Findings Summary**
- `critical_issues_total`: Across all workers
- `standard_violations_total`: Across all workers
- `suggestions_total`: Across all workers

### Output Format

Append a `_metrics` block to the final aggregated output:

```json
{
  "_metrics": {
    "execution": {
      "total_invocations": 8,
      "haiku_invocations": 7,
      "sonnet_invocations": 1,
      "escalation_rate": 0.125
    },
    "escalations": [
      {
        "partition": "AuthService.cs",
        "reason": "security_ambiguity",
        "original_model": "haiku",
        "escalated_model": "sonnet"
      }
    ],
    "workload": {
      "files_reviewed": 12,
      "partitions_created": 8,
      "technologies": ["csharp", "sql"]
    },
    "findings": {
      "critical": 1,
      "standard_violations": 4,
      "suggestions": 7,
      "positive_notes": 3
    },
    "cost_estimate": {
      "note": "Approximate based on typical token counts",
      "haiku_tokens_approx": 28000,
      "sonnet_tokens_approx": 4000,
      "estimated_savings_vs_all_sonnet": "~75%"
    }
  }
}
```

### Cost Estimation Heuristics

For approximate cost tracking without API-level instrumentation:

| Component | Estimated Tokens |
|-----------|------------------|
| Standards file (each) | ~2,500 |
| Average file diff | ~500-1,500 |
| Worker prompt overhead | ~300 |
| Worker response (typical) | ~800 |

Use these to estimate:
- `haiku_tokens_approx = haiku_invocations × (standards_tokens + avg_diff_tokens + overhead + response)`
- `sonnet_tokens_approx = sonnet_invocations × (same formula)`

### Savings Calculation

```
all_sonnet_cost = total_invocations × sonnet_rate
actual_cost = (haiku_invocations × haiku_rate) + (sonnet_invocations × sonnet_rate)
savings_percent = (all_sonnet_cost - actual_cost) / all_sonnet_cost × 100
```

Rate reference (per 1M tokens, as of skill creation):
- Haiku: ~$0.25 input / $1.25 output
- Sonnet: ~$3 input / $15 output

### Metrics Usage

The `_metrics` block enables:
- Comparing costs across PRs of different sizes
- Tuning escalation thresholds (if escalation_rate is too high, consider adjusting criteria)
- Identifying hot spots (which partitions consistently escalate?)
- Validating the model tiering strategy over time

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
