---
description: >-
  Fetch when reviewing a diff, pull request, or uncommitted changes, when
  preparing changes for commit or push, or when asked whether comments,
  XML docs, README/CLAUDE.md/AGENTS.md prose, specs, constitutions, or
  contract documents still match the code. Defines the documentation
  accuracy check: how to find every piece of prose that describes changed
  code, how to verify each claim against the current implementation, how
  to classify drift (stale, wrong, orphaned, contradicted), and the report
  format. Apply alongside the language standards, not instead of them.
---

# Documentation Accuracy Check

Required in any code review, and a recommended last step before pushing a
branch.

This check is about **truth**, not style. Whether a comment exists, how it is
worded, or whether it follows GhostDoc form is governed by the language
standards (for example `code/csharp-instructions`). This document only asks:
does the prose describe what the code actually does right now?

## What counts as prose

Any natural-language text that makes a claim about code, data, or behavior:

- XML documentation comments (`<summary>`, `<param>`, `<returns>`,
  `<exception>`, `<remarks>`, `<value>`) and JSDoc/TSDoc equivalents.
- Inline and block comments, including `// TODO` and `// HACK` notes.
- Attribute text read by tools or models: `[Description(...)]` on MCP tools and
  parameters, `[DisplayName]`, Swagger/OpenAPI summaries, validation messages.
- Log message templates and exception messages when they assert a cause or a
  state ("retrying because the token expired").
- Markdown that describes the code: `README.md`, `CLAUDE.md`, `AGENTS.md`,
  `docs/**`, `.specify/memory/*.md` (constitution, review guidelines),
  `specs/**` (feature specs, plans, `contracts/*.md`), ADRs.
- Comments in configuration: `appsettings*.json` sibling notes, Helm
  `values*.yaml` comments, pipeline YAML comments, `.editorconfig` notes.
- Front matter `description` fields in instruction documents and skills.
- The PR description and commit messages for the change under review.

## What counts as a claim

A claim is a statement that can be checked against the code. Break each piece of
prose into its claims and verify them one at a time. Typical claims:

| Claim type | Example |
|---|---|
| Behavior | "Returns null when the film is not found." |
| Order or sequence | "Providers run sequentially; TiVo first." |
| Default or limit | "Defaults to 3 retries." "Budget is 1000 calls per day." |
| Type, nullability, shape | "A list of IDs." "Never empty." |
| Error handling | "Throws `ArgumentNullException` if `id` is null." |
| Caller or callee | "Called once per batch by `BatchRunner`." |
| Location | "Registered in `ServiceCollectionExtension.cs`." "Lives under `Models/Generated/`." |
| Name | A config key, table, column, enum member, file, method, or flag named in prose. |
| Rationale or invariant | "Scoped because `DbContext` is not thread-safe." |
| Process | "Applied by the release's PreSync job, never by hand." |

Wording that makes no checkable claim ("helper for films") is not a finding
under this check. Report it only if the language standard requires something
more specific.

## Procedure

Work from the diff outward. Do not review only the lines that changed.

1. **Enumerate the change.** List every added, modified, deleted, or renamed
   symbol, file, configuration key, enum member, table, or endpoint in the diff.
   Include behavioral changes with no signature change (a reordered step, a new
   early return, a changed default).

2. **Find the prose that describes each item.** For each item in step 1:
   - Read the full member and its documentation comment, not just the hunk.
   - Read the file header comment and the containing type's `<summary>`.
   - Search the repository for the identifier's name (and its old name, if
     renamed) in `*.md`, comments, attribute strings, log templates, and
     configuration comments. A deleted or renamed symbol that still appears in
     prose anywhere is an orphan.
   - Search for prose that describes the item's role without naming it: the
     README section on the feature, the spec and contract documents for the
     feature branch, the constitution principle that governs the area.

3. **Verify new or changed prose against the code.** Everything the diff adds
   or edits in prose is a claim to check in the other direction. Confirm each
   named symbol exists and each described behavior matches the implementation.
   Check specifically for invented method names, wrong defaults, and
   over-stated guarantees.

4. **Classify every claim you identified** using the categories below. Record
   the accurate ones as well as the drifted ones, and the ones you did not
   settle.

5. **Decide which side is wrong.** When prose and code disagree, do not assume
   the code is right. Use "Wrong vs. Contradicted" below to decide which side
   to fix. Report the disagreement, state which side you believe should change,
   and say why. Only recommend rewriting the prose when the code change was
   clearly intentional and the prose is merely behind it.

6. **Check the change's own narrative.** The PR description and commit messages
   must describe the diff as it is. Flag scope that is described but not
   present, and present but not described.

## Classification

The category decides everything. There is no separate severity for a
documentation finding, and the Gate below reads these category names directly.

| Category | Meaning |
|---|---|
| **Stale** | Was true before this change; the change made it false. |
| **Wrong** | Was never true, or newly written and does not match the code. |
| **Orphaned** | Refers to a symbol, file, key, or document that no longer exists or was renamed. |
| **Contradicted** | Prose records an invariant or rationale that the code violates, and the prose is the side more likely to be right. Code may be the defect. |
| **Missing** | Prose that exists omits a fact that makes what it does say misleading. |
| **Unverifiable** | No amount of reading this repository settles the claim. Not a defect. |
| **Not checked** | You could have settled it and did not. Not a defect. Give the reason. |
| **Accurate** | Checked and matches. |

### Choosing between categories

- **Stale vs. Wrong.** Stale requires a prior state in which the prose was true.
  In a file the diff adds whole, there is no prior state: every drifted claim is
  **Wrong**, never Stale. Reserve Stale for prose that predates the diff.
- **Wrong vs. Contradicted.** Both mean prose and code disagree. The category
  turns on which side you would fix. Ask: *does the prose assert something the
  system is supposed to guarantee?* A rationale ("Scoped because `DbContext` is
  not thread-safe"), an invariant, a constraint traceable to a constitution
  principle, a contract document, or an external limit is **Contradicted** — the
  prose is evidence of intent and the code is the suspect. A plain description of
  mechanics with no stated "because" and nothing behind it is **Wrong** — the
  prose is the suspect. When you cannot tell, classify it Wrong and say in the
  recommendation that you could not establish intent.
- **Missing vs. the language standard.** Whether a member has a doc comment at
  all, and whether that comment carries every required tag, belongs to the
  language standard (`code/csharp-instructions`), not here. Do not report a
  member with no documentation, or a missing `<param>`, as Missing. Missing is
  narrower: the prose that *is* there leaves out a fact that makes the rest of it
  misleading. A `<returns>` describing only the returned value on a method that
  throws for a common input is Missing, because the description implies a total
  behavior the code does not have. A method with no XML documentation whatsoever
  is a finding for the language standard to make.
- **Unverifiable vs. Not checked.** Unverifiable means no amount of reading this
  repository would settle the claim: it depends on a runtime, an external
  service, a pipeline, or history. A claim you *could* settle by opening another
  file but did not — because of scope, time, or a constraint on the review — is
  **Not checked**. Never bank a scope limitation as Unverifiable. Both get a row
  in the Claims checked table, with the reason in the result cell.
- **An undocumented rationale still counts as intent.** A "because" or "so
  that" clause naming a specific consumer, downstream requirement, or
  constraint is evidence of intent even when it traces to no document —
  "ordered by title so the admin grid renders alphabetically" names a real
  consumer. Classify it **Contradicted** and add a Not checked row for the
  consumer claim so the author confirms which side to fix. A rationale that
  names nothing you could check ("done this way for performance", "kept simple
  on purpose") is not evidence of anything: if the surrounding claim is false,
  it is **Wrong**.
- **A guarantee the code does not enforce is Wrong, not Unverifiable.** Prose
  asserting "never empty", "always sorted", "unique", or "never null" states a
  contract. Judge it against enforcement, not against runtime data: if nothing
  in the code path checks, filters, or constrains the value into that shape, and
  nothing upstream in the repository guarantees it, the claim is **Wrong** —
  the prose promises a contract the code does not provide.

### Granularity

One finding per **claim**, not per comment block. A single `<summary>` asserting
three things that are each false is three findings. Group only when one root
cause produces the same false claim in several places, and then list every
location under that finding.

## Rules

- **Quote the prose verbatim** and cite it as `File.cs:line`. Cite the code
  that contradicts it the same way. A finding without both citations is not
  a finding.
- **Do not paraphrase code behavior from the diff alone.** Read the
  implementation. If a claim spans files (a caller, a config binding, a table),
  open them.
- **Do not flag wording, tense, or tone.** Only truth.
- **Do not flag what a linter or compiler already fails the build on.**
- **Never mark a claim accurate that you did not check.** If the review is
  time-boxed, list what was not checked.
- **Do not silently "fix" prose to match the diff** when performing the check
  as a pre-push step. Propose the rewrite; the author confirms which side is
  the intended behavior.
- **Generated files are out of scope** (scaffolded EF models, designer files,
  lock files). Prose that describes how they are generated is in scope.

## Report format

Add this section to the code review report, or produce it standalone when the
check is run on its own. The Claims checked table is required even when empty.

Close with a scope line naming any region of prose you did not search, and give
it a bound. Omit an omission that would be true of every review; "callers outside
this solution" tells a reader nothing.

Derive every category from "Choosing between categories" above. Do not copy the
categories used in the example below. List the findings that fail the Gate
first. Do not label a documentation finding with a severity, and do not file it
under a code review's severity headings.

```
## Documentation Accuracy

### Findings

#### 1. Stale summary on FilmRepository.GetAsync
**Prose**: `FilmRepository.cs:41` — "Returns null when the film is not found."
**Code**: `FilmRepository.cs:48` now throws `FilmNotFoundException`; no null path remains.
**Also affected**: `README.md:112` repeats the null-return claim.
**Recommendation**: Update both, or restore the null return if callers depend on it
(`FilmService.cs:77` still null-checks the result — see Contradicted below).

#### 2. Contradicted invariant in ServiceCollectionBuilder
**Prose**: `ServiceCollectionBuilder.cs:63` — "OpsContext is Scoped; never resolve from the root provider."
**Code**: `RunRecorder.cs:29` resolves `OpsContext` from `IServiceProvider` injected as a singleton.
**Recommendation**: The prose records a constitution rule. The code is the defect.

### Claims checked

| Location | Claim | Result |
|---|---|---|
| `FilmRepository.cs:41` | Returns null when not found | Stale |
| `ServiceCollectionBuilder.cs:63` | OpsContext never from root | Contradicted |
| `BatchRunner.cs:18` | Providers run sequentially | Accurate |
| `values.production.yaml:9` | Schedule keeps OMDB under 1000/day | Accurate |
| `specs/004-run-ledger/contracts/outcome.md` | Lists all `ExecutionRunOutcome` members | Missing — `BudgetExhausted` added, not listed |
| `README.md:40` | Image pushed to ACR on every main build | Unverifiable — pipeline runs outside repo |
| `TitleMapper.cs:88` | Alternate titles are deduplicated | Not checked — needs the SGC collation, out of scope |

**Scope**: comments in `Publicity.Processor.Legacy/**` were not searched, 340 files
outside the diff's blast radius.
```

## Gate

The check **fails** when any finding is classified Stale, Wrong, Orphaned, or
Contradicted, wherever that prose lives. Missing, Unverifiable and Not checked
do not fail the gate but must appear in the report. A report with no "Claims
checked" table, or no scope line, is incomplete.
