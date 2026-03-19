---
name: jira
description: Create and manage Jira tickets using Atlassian MCP server tools (mcp__atlassian__jira_*). Use when the user asks to create a Jira ticket, file a bug, create a feature request, log technical debt, add an improvement, or any task involving Jira issue management. Triggers on mentions of "Jira", "ticket", "issue", "bug report", or "feature request" in the context of project tracking.
---

# Jira Ticket Management

Use `mcp__atlassian__jira_*` MCP tools for all Jira operations.

## Supported Projects

| Project Key | Description |
|-------------|-------------|
| **ISFS** | Internal Systems & Fulfillment Services (default) |
| **SLS** | Streaming License Server |

Use `AskUserQuestion` to ask which project if not specified. Default to **ISFS**.

## Ticket Creation Workflow

1. Gather requirements from user (summary, description, type)
2. Determine issue type (see below)
3. Use the `AskUserQuestion` tool to ask: "Would you like to add acceptance tests to this ticket?"
4. If yes, write acceptance tests using Given/When/Then syntax and include in the description
5. Ask about component assignment — load the appropriate component list for the selected project
6. Create the ticket via `mcp__atlassian__jira_create_issue`

## Issue Types

| Type | Use When |
|------|----------|
| `ProdBug` | Production bugs |
| `New Feature` | Net-new functionality |
| `Improvement` | Enhancements to existing features |
| `Technical Debt` | Modernization, refactoring |
| `Task` | General work items |

## Default Properties

- **priority**: Prefer `Minor` unless user specifies otherwise
- **assignee**: `abarker@swankmp.com` (unless user specifies otherwise)
- **components**: Match from the project's component list (see Resources below)

## Acceptance Tests (Optional)

Use `AskUserQuestion` to confirm before adding. When the user opts in, format tests in the description as:

```
h3. Acceptance Tests

* *Given* [precondition]
* *When* [action]
* *Then* [expected result]
```

Use Jira wiki markup (not markdown) in issue descriptions.

## Example

User: "Create a ticket for adding retry logic to the Tv Device Api"

→ Issue type: `Improvement`
→ Component: `Tv Device Api`
→ Priority: `Minor`
→ AskUserQuestion: "Would you like to add acceptance tests to this ticket?"
→ Create with `mcp__atlassian__jira_create_issue`

## Resources

- **[references/isfs-components.md](references/isfs-components.md)** — ISFS project components. Read when assigning components to ISFS tickets.
- **[references/sls-components.md](references/sls-components.md)** — SLS project components. Read when assigning components to SLS tickets.
