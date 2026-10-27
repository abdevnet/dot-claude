---
description: >-
  Fetch when reviewing code, a diff, a pull request, or a branch before merge,
  and when investigating a bug or judging a refactor. Contains the 35 review
  lenses in five categories: Security (S1-S8), Performance (P1-P6),
  Readability (R1-R6), Debugging (D1-D8) and Refactoring (F1-F7). Each lens
  says what to hunt for and what a finding in that category must contain.
---

# Code Review Lenses

Thirty-five lenses for finding problems, grouped into five categories. Adapted
from prompt-architects.com, "56 AI Prompts for Code Review & Debugging":
<https://prompt-architects.com/blog/56-ai-prompts-for-code-review-debugging>.

These say what to look for. They carry no Swank rules and no precedence of their
own. `review/code-review-instructions` supplies the workflow, the precedence
order and the report format; the language standards supply the rules. Where a
lens suggestion contradicts a Swank standard, the standard wins and the
suggestion is dropped.

## Which categories apply

| Category | Apply when |
|---|---|
| Security, Performance, Readability | every review of changed code |
| Debugging | the change is a bug fix, or the review turns into an investigation |
| Refactoring | the change restructures existing code, or you are proposing that it should |

Name the lens a finding came from in the report's `*Standard:*` line, as the
identifier plus its subject, for example `R5 (DRY and duplication)`. Use the
report format from `review/code-review-instructions`; do not add a category
field it does not have.

## Across all lenses

Report problems with concrete consequences, not taste or abstract risk. Skip
anything a formatter or linter catches. Calibrate against the conventions the
repository actually uses, not generic best practice. Saying a section is sound
and should be left alone is a valid finding.

---

## Security

**S1. General security audit.** Trace attacker-controlled data from entry point
to sink. Distinguish authentication (who are you) from authorization (are *you*
allowed *this*); the gap between them is where real vulnerabilities live. Every
finding names what an attacker concretely gains, the attack path, and a fix,
ranked by severity. Never invent CVE numbers. If the code is sound, say so and
stop.

**S2. Input validation.** Validate at trust boundaries, not deep in the call
stack. Identify the boundaries first: deserialized third-party payloads,
inbound requests, file and share contents, inter-process messages, configuration
values, operator input. Probe the edges: empty, null, missing keys, wrong types,
oversized values. Distinguish validation (rejecting bad data) from sanitization
(transforming it). Error paths must not leak sensitive detail. Output should
work as a checklist that maps to work items.

**S3. Authentication and authorization gaps.** For each entry point ask both
questions separately: is the caller authenticated, and is this caller allowed
this specific resource? Hunt insecure direct object reference, where the caller
supplies an identifier and nothing checks ownership. Authorization runs
server-side on every request. For a component with no inbound surface, the
question inverts: which credentials does each outbound call carry, and does the
code ever send one somewhere it should not, such as a key in a log line. Flag
explicitly what cannot be assessed from code alone.

**S4. Injection.** Parameterized *values* are safe; *identifiers* such as table
names, column names and sort targets are not parameterizable and need
allowlisting. Watch raw-SQL escape hatches, string-built queries, and SQL
embedded in literals inside application code, including the SQL that migrations
emit. Every finding includes the exact input that exploits it. No generic
warnings.

**S5. Secrets exposure.** Hardcoded credentials, private keys, secrets in logs
or comments, server-side keys reaching client-visible surfaces. Never print a
discovered secret; reference its location and type only. Remediation includes
rotation and history cleaning, not just deletion.

**S6. Dependency vulnerabilities.** Never assert specific CVEs from memory. Mark
version claims as needing a scanner. What a review can assess: unpinned version
ranges, unmaintained packages, and binaries committed to the repository that no
scanner watches. Prioritize by exposure; code on a request or external-call path
outranks build-time tooling.

**S7. OWASP Top 10 walk.** Walk every category explicitly, including the
inapplicable ones. Each category either cites specific at-risk code, states that
nothing was found, or says why it does not apply. Mark the categories that
cannot be assessed from application code, such as logging and monitoring,
deployment configuration and supply chain. Rank by exploitability in this
deployment.

**S8. Rate limiting and quota surface.** Two directions. As a server: find cheap
or unauthenticated calls that trigger expensive work, and unbounded input sizes.
As a client: check that budgeted calls stay inside the budget, that retries
count against it, and that a spin loop cannot burn a day's quota. Note where a
limiter itself becomes a denial of service by locking out legitimate callers.
An in-memory counter does not enforce a limit across replicas or processes.

---

## Performance

**P1. General bottleneck scan.** Without profiler data every finding is a
labeled hypothesis with the cheapest way to measure it. Look for queries inside
loops, synchronous I/O on a hot path, needless serialization, unbounded
collections held for a long lifetime, and repeated recomputation. State the
ceiling of each fix: optimizing a path that is 5% of runtime buys at most 5%.

**P2. Database query performance.** Work from execution-plan output, naming the
specific problem (scan, join order, non-sargable predicate) before the fix. A
proposed index states its write cost and footprint. Verify a rewrite does not
change semantics around nulls, duplicates or ordering. Per query: problem, fix,
expected effect, and what to measure afterward.

**P3. Memory usage and leaks.** Separate leaks from legitimate caching and
normal garbage collection. Classic retainers: event handlers never
unsubscribed, timers never disposed, unbounded caches keyed by request data,
closures capturing large scopes inside long-lived objects, and per-item state
accumulating in a singleton across a long run. Without heap snapshots, prescribe
what to capture and when.

**P4. Algorithm complexity.** State complexity with its n; "O(n²)" is
meaningless without saying what n is. Judge against real input sizes. Expose
hidden costs such as membership checks against a list inside a loop, or string
concatenation in a loop. Each improvement shows the complexity change and the
readability cost.

**P5. Async and concurrency.** Assume anything that can interleave eventually
will, in production. Find check-then-act sequences on shared state, and examine
every await point for data that may be stale afterward. Distinguish
single-process re-entrancy from true parallelism, and per-process fixes from
cross-instance ones. A per-process counter does not enforce a global cap.

**P6. Caching opportunities.** Caching is a correctness liability to justify,
not a default fix. Every candidate specifies what is cached, the key, the
lifetime, and exactly what happens when the source changes. Never cache
user-specific or instance-specific data under a shared key. Estimate the hit
rate, and consider fixing the slow underlying operation instead of masking it.

---

## Readability

**R1. General readability.** Review as the engineer who has to change this code
next. Silent on taste, direct about genuine confusion. Flag misleading names,
functions doing unrelated jobs, deep nesting, bare boolean arguments at call
sites, and unexplained magic values where a named constant exists. Test: would a
competent developer misread this, or need multiple passes? State the specific
confusion caused, and name what reads well and should be left alone.

**R2. Function complexity and single responsibility.** Split a function when it
helps a reader, not to hit a line count. Try stating its job in one sentence
with no "and". Watch for mixed abstraction levels in one body, such as transport
plumbing next to domain rules next to persistence. Recommend an extraction only
if it has an obviously good name and a short parameter list; needing six
parameters means the split point is wrong.

**R3. Naming.** Renaming is cheap before merge and expensive once public.
Misleading outranks terse: does the name match what the thing does now? Check
vocabulary consistency with the domain and do not introduce synonyms for terms
the codebase already uses. Booleans read as predicates. Renames of contract
surfaces such as published interfaces, routes, configuration keys and closed
vocabularies are breaking changes; flag them as such. Skip conventional idioms
like loop counters.

**R4. Documentation and comment quality.** Most comments are noise, the missing
ones are expensive, and stale documentation misleads more than absence.
Recommend deleting a comment that restates the code, unless a language standard
requires it, in which case the standard wins. Hunt the missing "why": a
deliberate oddity with no explanation dies at the next refactor. Suggest the
content, not just "add a comment". For whether prose still matches the code, use
`review/documentation-accuracy-instructions`; that check is separate and has its
own gate.

**R5. DRY and duplication.** The wrong abstraction costs more than duplication.
True duplication is the same *knowledge* in two places that must change in
lockstep, and only that justifies extraction. Code that merely looks alike, or
whose copies are already diverging, should stay duplicated; say so explicitly.
Test: can you name the shared concept without a flag parameter that switches
behaviour per caller? State the coupling cost alongside the benefit.

**R6. Error handling completeness.** Review as the engineer reading the log at 3
a.m. with nobody watching a debugger. Hunt empty catch blocks, catches that log
nothing, unawaited tasks and unobserved task exceptions. Every external call
needs a failure path. Ask what happens on *partial* success, where one half of
an operation committed and the other did not. Classify recoverable against
unrecoverable and check the code treats them differently. Messages carry
debugging context without leaking secrets or internals. Every finding needs a
concrete failure scenario.

---

## Debugging

Apply when reviewing a bug fix, asking whether it addresses the root cause or
silences the symptom, or when a review becomes an investigation.

**D1. Error message analysis.** Separate what the message proves from what is
inferred, and label the inferences. Explain what the error actually means rather
than its surface symptom; a vendor's generic status code often has a specific
documented cause. Propose the check that distinguishes between candidate causes.
Reject a fix that merely silences the error.

**D2. Stack trace interpretation.** The throwing line rarely contains the broken
assumption. Find the first in-application frame, follow "caused by" chains to
the origin, and account for the frames that async and middleware pipelines
remove. Output: the root-cause frame, the chain, what information is missing, and
the next confirmation step.

**D3. Root cause via five whys.** Each "why" must follow from evidence, not from
a plausible story; a plausible story that fits the symptom is the most common
wrong answer. Continue past the first satisfying answer. Separate the trigger
from the underlying condition, and treat "why did we not detect it sooner" as
its own branch. Systems, not blame.

**D4. Race condition analysis.** Reason about interleavings instead of re-running
and hoping. Enumerate every shared mutable thing and every await or yield point,
then construct the exact sequence that produces the symptom. If you cannot
construct it, say so rather than guess. Prefer removing shared state over adding
locks.

**D5. Regression analysis.** Rank recent changes by plausibility for this
specific symptom, including non-code candidates: dependency updates,
configuration changes, deployment or chart version bumps, feature flags,
upstream data drift. Recommend a bisect strategy and the evidence that
eliminates each candidate. Do not revert a correct change just because it is
recent.

**D6. API contract mismatch.** Integration bugs are disagreements about
contracts nobody wrote down. Compare payloads field by field: presence, type,
nullability, casing, format, nesting. Hunt quiet mismatches such as numbers sent
as strings, or null against a missing key. Establish which side changed.
Recommend boundary validation so the next mismatch fails loudly.

**D7. Silent failure detection.** Hunt failures that do not announce themselves:
empty catches, fire-and-forget calls, unchecked return values, and batch loops
that continue past a failed item without recording it. Distinguish
logged-but-unmonitored from never-recorded. Output: each swallowing point, what
is assumed rather than confirmed to succeed, and the assertion or alert that
would surface it.

**D8. Variable state tracing.** Bisect instead of reading everything. Map every
point a value is read, written, transformed or passed, mark the last known-good
and first known-bad points, and pick the check that bisects that range fastest.
Prescribe specific log lines and breakpoints, not "add more logging".

---

## Refactoring

Apply when the change restructures existing code, or when proposing
restructuring as a suggestion.

**F1. Behaviour-preserving refactor.** If coverage is thin, recommend
characterization tests first. Preserve observable behaviour exactly, including
error types, messages and edge cases. Work in small independently shippable
steps. A suspected bug found mid-refactor gets flagged, not silently fixed. No
scope creep into unrelated cleanup.

**F2. Extract function.** A bad extraction is worse than a long function. The
extracted piece must have a name that says what it does independent of its
original context, few parameters, and where possible purity. Preserve early
returns and error paths. Deliver the extracted function with its signature, the
updated caller, and where it should live.

**F3. Design pattern suggestion.** Reach for a pattern to solve a demonstrated
problem, not to demonstrate knowledge. First assess whether a pattern is
warranted at all. Name the specific pain it removes and its concrete cost, and
give the simplest solution first; a lookup table or a function usually beats a
pattern. Respect the conventions the codebase already uses.

**F4. Dependency injection refactor.** Introduce seams with the lightest
mechanism that works: a default parameter beats a constructor argument, which
beats a container registration. Do not create an interface for a single
implementation unless a standard or constitution requires it, in which case that
requirement wins. Keep existing call sites unchanged via real-implementation
defaults. Hunt hidden dependencies: clocks, randomness, environment, static
state. Name the test the seam unlocks.

**F5. Error handling upgrade.** Design for three audiences with different needs:
the operator (what do I do now), the calling code (can I retry), and whoever
reads the log later (what exactly happened). Distinguish expected failures from
unexpected ones, preserve inner causes when wrapping, keep the approach
consistent within a layer, and state the retry policy explicitly.

**F6. Type safety improvement.** Strengthen types where they catch real bugs,
not for coverage. Prioritize the boundaries where untyped data enters:
deserialized payloads, configuration strings, nullable columns. Prefer making
illegal states unrepresentable over adding runtime checks. Rank unchecked casts
and null-forgiveness by how exposed they are to external input, and say which
improvements are not worth making.

**F7. Dead code elimination.** Rate confidence per item and bound the claim, for
example "unused within this solution". Public surface is reachable by consumers
you cannot see, so removing it is a breaking change. Check non-obvious call
sites: tests, scripts, configuration, CI, installers. Dynamic dispatch,
runtime composition and string-based binding hide usage, so "no references" in
an editor proves nothing. Provide the verification command for each removal, and
separate safe-now from needs-checking.
