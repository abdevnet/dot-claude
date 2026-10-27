---
description: >-
  Fetch when reviewing code, a diff, a pull request, a branch before merge, or
  uncommitted changes — including when the request does not use the word
  "review" ("what do you think of these changes?", "anything wrong with this
  before I merge?", "PR feedback?"). Defines the review workflow: how to
  establish the change set, which standards to load from the catalog, the
  required documentation accuracy pass, how project-local review documents and
  constitutions take precedence, severity definitions, and the report format.
  This document is the workflow only. The rules live in the standards
  documents, which must be fetched alongside it.
---

# Code Review Workflow

## Step 1 — Establish the change set

If the requester pasted code or named a specific pull request, review that and
skip to Step 2. Otherwise derive the diff:

1. `git fetch origin --prune`.
2. Pick the base branch. Try `origin/main`, then `main`, then `origin/develop`,
   then `develop`. Ask if none resolve.
3. `git diff --unified=1 --no-color <base>...HEAD`.

Record the base and head — the report names both. If the diff runs beyond
roughly two thousand lines, say so and ask for a narrower scope rather than
reviewing thinly across all of it.

## Step 2 — Load the applicable standards

Call `get_catalog` **before** reading the diff for findings. Fetch every catalog
document whose description matches the change, using `get_document`. Match on
what the code *does*, not on its file extension alone: SQL embedded in a C#
string is SQL, and a `.cs` file that builds an outbound HTTP call is subject to
the HTTP client standard as well as the C# standard.

Fetch several documents when the change spans several areas. If a document
cannot be retrieved, say so plainly in the report's unverified section and do
not substitute a remembered version of its rules.

Always fetch `review/code-review-lenses-instructions` as well. It carries the
thirty-five lenses Step 4 hunts with, and it decides which of its categories
apply to this change.

## Step 3 — Run the documentation accuracy pass

**Required. Not a dimension of Step 4, and not skippable.**

Fetch `review/documentation-accuracy-instructions` and follow it against the
change set from Step 1. It defines what counts as prose, what counts as a
checkable claim, how to search outward from the diff, how to classify drift, and
its own gate.

Its findings are reported in their own section with their own tables, not folded
into the severity lists.

## Step 4 — Review the code

Walk the hunks in this order: **correctness, security, reliability, standards,
maintainability.**

A finding requires evidence. Quote the offending lines verbatim. If you cannot
quote it, drop it.

Do not skim past the stylistic mismatches the standards documents actually
cover: namespace style, structured logging templates versus string
concatenation, guard-clause helpers versus string-literal parameter names,
async methods missing a cancellation token, identifier bracketing and
constraint naming in SQL.

## Step 5 — Apply project-local review documents

Check the repository under review for its own review material and apply it in
addition to the catalog standards:

- `.specify/memory/code-review-guidelines.md`
- `.specify/memory/constitution.md`
- `docs/code-review*.md` or `CODE_REVIEW*.md` at the repository root
- the repository's own `CLAUDE.md`, and any `CLAUDE.md` in the directory being
  changed

These may define additional finding categories and project gates. The review
lenses themselves come from the catalog, not from here. When a guidelines
document defines categories, tag every finding with its category. When it
defines mandatory report sections or gate tables, produce them even when
nothing is found.

**Precedence on any conflict, highest first:**

1. The Swank standards from this catalog.
2. The project's constitution.
3. The repository's `CLAUDE.md`.
4. The project's review guidelines.
5. This document.

Example: a readability lens suggests deleting a comment for restating the code,
while the C# standard requires XML documentation on non-private members. The
standard wins, and the suggestion is dropped rather than reported.

## Severity

For Step 4 findings only. Step 3's documentation findings carry a category
instead of a severity, and its own gate decides whether they fail the review.

- **Critical** — proven security vulnerability, data loss, authorization bypass,
  or a breaking change to a published contract.
- **High** — a clear bug, crash, or incorrect behavior.
- **Medium** — a standards violation, a moderate maintainability problem, or a
  risky gap in test coverage.
- **Low** — style, a minor refactor, an optional improvement.

When a finding sits between two severities, assign the lower one and say why it
might be higher.

## Report format

```
# Code review: <head> vs <base>

## Summary
One to three sentences. End with a verdict: **Approve**, **Comment**, or
**Request changes**.

## Documentation Accuracy
The section produced by Step 3, including its required tables.

## Findings
### Critical
### High
### Medium
### Low

Each finding:
**<title>** — `path:lines`
A fenced block with the verbatim snippet, six lines or fewer.
*Why:* one or two sentences naming the concrete consequence.
*Standard:* the catalog document, the project document, a lens identifier
and its subject such as `R5 (DRY and duplication)`, or BestPractice.
*Fix:* a small diff or concrete steps.

## Positive notes
## Unverified
```

Drop empty severity sections rather than writing "none found" under each.
`Positive notes` and `Unverified` are optional — include them when you have
content. Use `Unverified` for standards you could not fetch, claims you could
not settle, and anything that needs a scanner or a profiler rather than a
reading.

A review with no findings is valid output. Write the summary, the documentation
accuracy section, a verdict of **Approve**, and stop.

## Rules

- Report problems with concrete consequences, not matters of taste. Say plainly
  when a section is sound and should be left alone.
- Skip anything a formatter or linter already catches.
- Never invent a CVE number, a rule, or a standard's wording, and never cite a
  standard whose text is not in context. Mark version and vulnerability claims
  as needing a scanner.
- Cite every finding as `path:line`.
- Review, do not rewrite. Report the finding and propose the fix; apply changes
  only when asked to.

## Gate

The review fails when any of these is true. Say which one, and why.

1. The documentation accuracy gate from Step 3 fails, which its own document
   decides from its category names.
2. A Critical or High finding from Step 4 stands.
3. A project gate from Step 5 fails.

These are counted separately. A documentation finding fails the review through
the first only, never the second.
