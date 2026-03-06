# Metrics Collection

After aggregation, collect and output execution metrics.

## Counters to Track

**Worker Invocations**
- `haiku_invocations`: Tasks sent to Haiku
- `sonnet_invocations`: Tasks sent to Sonnet (escalations only)
- `total_invocations`: Sum of all worker calls

**Escalation Tracking**
- `escalation_count`: Number of Haiku to Sonnet escalations
- `escalation_reasons`: List of reasons (unknowns, low_confidence, conflicts, security_ambiguity)

**Workload Distribution**
- `files_reviewed`: Total files processed
- `partitions_created`: Number of work partitions
- `files_per_partition_avg`: Average files per worker task

**Findings Summary**
- `critical_issues_total`: Across all workers
- `standard_violations_total`: Across all workers
- `suggestions_total`: Across all workers

## Output Format

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
    }
  }
}
```
