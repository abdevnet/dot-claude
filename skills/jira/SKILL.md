---
name: jira
description: Create and manage Jira tickets using whichever Atlassian MCP server is available in the session. Use when the user asks to create a Jira ticket, file a bug, create a feature request, log technical debt, add an improvement, or any task involving Jira issue management. Triggers on mentions of "Jira", "ticket", "issue", "bug report", or "feature request" in the context of project tracking.
---

# Jira Ticket Management

Use whichever Atlassian MCP Jira tools are available in the current session for all Jira operations. Common server prefixes include `mcp__atlassian__*` (local Docker-backed) and hosted variants like `mcp__<uuid>__*JiraIssue*`. Pick any one that exposes equivalent create/search/update/transition operations.

The site is `swankmp.atlassian.net` — pass that (or the equivalent cloudId) as required by the chosen server.

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
4. If yes, write acceptance tests using Given/When/Then syntax and pass via `customfield_12901` in `additional_fields`
5. Use the `AskUserQuestion` tool to ask: "Should this ticket be assigned to you or left unassigned?"
6. If assigned, use `abarker@swankmp.com`. If unassigned, omit the `assignee` parameter.
7. Ask about component assignment — load the appropriate component list for the selected project
8. Create the ticket via the chosen server's create-issue tool (e.g. `mcp__atlassian__jira_create_issue` or `createJiraIssue`)

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
- **assignee**: Ask user — either `abarker@swankmp.com` or unassigned
- **components**: Match from the project's component list (see Resources below)

## Acceptance Tests (Optional)

Use `AskUserQuestion` to confirm before adding. When the user opts in, write acceptance tests using Given/When/Then syntax and put them in the **dedicated custom field**, NOT in the description.

- **Custom field**: `customfield_12901` (named "Acceptance Tests")
- **Pass via `additional_fields`** on create, e.g.: `{"priority": {"name": "Minor"}, "customfield_12901": "- Given ... When ... Then ...\n- Given ... When ... Then ..."}`
- **Format**: Plain text with `- Given ... When ... Then ...` per line (one test per line, separated by newlines)
- Keep the description for context, scope, and requirements only — no acceptance tests in the description.

## Example

User: "Create a ticket for adding retry logic to the Tv Device Api"

→ Issue type: `Improvement`
→ Component: `Tv Device Api`
→ Priority: `Minor`
→ AskUserQuestion: "Would you like to add acceptance tests to this ticket?"
→ Create via the available Atlassian create-issue tool

## Resources

- **[references/isfs-components.md](references/isfs-components.md)** — ISFS project components. Read when assigning components to ISFS tickets.
- **[references/sls-components.md](references/sls-components.md)** — SLS project components. Read when assigning components to SLS tickets.
