---
name: swank-code-review
description: >
  Reviews a diff, pull request, branch, or set of files against the Swank
  coding standards (C#, ASP.NET Core, data access, HTTP clients, console apps,
  Angular/TypeScript, SQL Server, unit and acceptance tests, comments), the 35
  review lenses, and the documentation accuracy gate. Use for any review of
  Swank code, including when the request does not say "review": "what do you
  think of these changes", "anything wrong before I merge", "PR feedback",
  "compare my branch to main". Prefer this over the built-in /code-review for
  Swank repositories, because that one does not know the Swank standards.
---

# Swank Code Review

A single-pass review in the current context. The reviewer reads the real files, loads the standards that match what the code does, and reports in the catalog's format. There is no partitioning, no worker agents and no escalation ladder: the model doing the review holds the whole diff and the applicable standards at once, and the findings most worth making (an interface, its implementation and its caller disagreeing) need all the files in one head.

The workflow itself is `references/standards/code-review-instructions.md`. Read it first. This file only says how to apply it with the local copies of the catalog.

## 1. Establish the change set

Follow Step 1 of the workflow doc. If nothing was pasted or named: `git fetch origin --prune`, pick the base, diff `<base>...HEAD`, and record both for the report. There is no size cap. Review the whole change set, ignore the workflow doc's prompt to narrow scope past two thousand lines, and state the diff's line count in the report so the reader knows what was covered.

Collect the PR description, ticket, or commit messages too. They give findings context and are themselves checked in step 4. When the branch name carries a Jira key, fetch the ticket with the Atlassian tools; until a PR exists it is the change narrative.

## 2. Load standards

The catalog is mirrored verbatim in `references/standards/`, and `scripts/sync-standards.sh` refreshes it from the ai-instructions repo. Where the workflow doc says `get_catalog` and `get_document`, read the local files instead.

Read [references/standards-selection.md](references/standards-selection.md) and load every document whose signal appears in the change. From inside the repository, `scripts/standards-signals.sh <base> [head]` prints which signals the diff contains. Read the standards two or three files per call: tool output beyond roughly 40KB is spooled to a file and costs a second read, and a large diff behaves the same way. Always load `code-review-lenses-instructions.md` and `comments-instructions.md`. Match on what the code does, not the extension: SQL in a C# string is SQL, and a `.cs` file that builds an outbound HTTP call gets the HTTP client standard as well as the C# one. When unsure whether a document applies, load it. The whole catalog is about 48k tokens, so an extra standard costs far less than a missed rule.

Never cite a rule from memory. If a document is missing locally, say so under Unverified.

## 3. Review

Follow Steps 4 and 5 of the workflow doc. Read whole files, not just hunks, and open callers and config when a hunk's correctness depends on them. That includes sibling repositories under `~/projects` when an invariant lives there, such as a database project's table scripts or the upstream API a comment claims to match; a schema file settles what a guess cannot. Quote the offending lines verbatim; a finding you cannot quote is dropped.

Lens categories: Security, Performance and Readability always; Debugging when the change is a bug fix; Refactoring when the change restructures existing code. A lens suggestion that contradicts a standard is dropped, because the standards carry the team's decisions and the lenses only say where to look.

## 4. Documentation accuracy pass

Required, reported in its own section, never folded into the severity lists. Load `documentation-accuracy-instructions.md` and follow it. Grep outward from the diff for prose that names a changed symbol, file, or config key: doc comments, README, CLAUDE.md, AGENTS.md, `docs/**`, `specs/**`, contracts. The Claims checked table and the scope line are required even when nothing was found.

## 5. Report

Use the workflow doc's report format, severities, precedence and gate as written. When a gate fails, say which one.

When the repository's test suites run locally in a few minutes, run them and report the counts under Positive notes or Unverified. A green suite is evidence for the review, not a verdict on its own.

If the user asks for findings in the IDE's finding list, send the severity findings through `ReportFindings` and keep the documentation accuracy section in the markdown, since that tool has no category field.

## When to fan out instead

Stay in-thread by default. Use a separate agent only when:

- this session wrote the code and the user wants an independent read. Spawn `code-review-agent` with the repository path, base and head, and nothing else. Passing your own conclusions would anchor the read you asked for.
- the diff is too large to hold alongside the standards in one context. Split it by file group, run one `code-review-agent` per group in parallel (the Workflow tool fits this), then merge the reports and dedupe by file and line.

In both cases the agent follows this skill. The format and the gate do not change.
