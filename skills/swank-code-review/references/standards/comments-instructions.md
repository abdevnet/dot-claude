---
description: >-
  Fetch when generating, reviewing, or modifying code in any language, when
  writing a commit message, a pull request description, or markdown
  documentation. Defines the Swank standard for what a comment must contain,
  the comment shapes that are noise, the rule against deleting existing
  comments you cannot explain, and the comment length rule. Does not override
  documentation that a language standard requires, such as the XML
  documentation in code/csharp-instructions.
---

# Comment and Prose Standards

Applies to every language, and to prose in commit messages, pull request
descriptions, and markdown documents.

This document governs what a comment **says**. Two other documents govern
neighboring concerns and win where they apply:

- Documentation a language standard **requires**. A standard always wins over
  this document. Examples, not an exhaustive list: XML documentation on
  non-private members in `code/csharp-instructions`; the `// == SECTION ==`
  component comments in `code/angular-instructions`; the stored procedure
  header block and the commented-out `DECLARE` template in
  `database/sqlserver-instructions`; the bearer token source comment in
  `code/productpublicityapi-instructions`; the `// Arrange`, `// Act`,
  `// Assert` markers in the testing standards. Check the standards for the
  language you are writing before deciding a comment is noise.
- Whether existing prose still **matches** the code —
  `review/documentation-accuracy-instructions`.

## The test

**A comment must say something the code cannot say.** Apply the test to each
comment you write. There is no target count.

A comment passes when it carries one of these:

- Why this approach, when an obvious alternative was rejected.
- A constraint from outside the file: a vendor quirk, an upstream contract, a
  measured performance result, a business rule.
- An invariant the types do not enforce.
- A required ordering or a non-obvious consequence.
- A workaround, with the ticket that will remove it.

A comment fails when it restates the code. Delete it rather than reword it.

## Comments that fail the test

**Narrating the next line.**

```csharp
// Bad
// Increment the retry count.
retryCount++;

// Loop through the films.
foreach (var film in films)
```

```csharp
// Good — the reason is not recoverable from the code.
// GTMS rejects the batch when a title repeats, so dedupe before the call.
var distinctTitles = titles.Distinct().ToArray();
```

**Restating the signature.** The XML documentation is still required; the extra
inline comment is not.

```csharp
// Bad
/// <summary>
/// Gets the active films for a studio.
/// </summary>
// Gets the active films for the given studio ID.
public async Task<IReadOnlyList<Film>> GetActiveFilmsAsync(int studioId)
```

**A banner sectioning a long method.** A method that needs internal section
headers needs to be two methods. Extract instead of labeling.

```csharp
// Bad
public async Task ProcessAsync()
{
    // ---------- validate ----------
    // ...

    // ---------- persist ----------
    // ...
}
```

```csharp
// Good
public async Task ProcessAsync()
{
    Validate();
    await PersistAsync();
}
```

This does not apply to the section comments a standard requires, such as the
Angular component ordering comments.

**Restating a name.**

```typescript
// Bad
// The film service.
private readonly filmService = inject(FilmService);
```

```sql
-- Bad
-- Select the films.
SELECT  f.FilmId
```

```sql
-- Good
-- NOLOCK is deliberate: this feeds the nightly report and a dirty read is
-- cheaper than blocking the publicity writers. See ISFS-4102.
SELECT  f.FilmId
FROM    dbo.Film f WITH (NOLOCK)
```

## Say it in fewer words

Applies to comments and to prose alike. **Do not use a hundred words where
twenty will do.** Write the shortest version that still carries the fact, then
delete what is left over.

- Cut every word that does not change what the reader understands. No preamble,
  no restating the point in a second sentence, no hedging.
- Prefer a clause to a sentence and a sentence to a paragraph.
- A comment is one or two lines. When the reason needs more, put it in the
  commit message or a ticket and point the comment at it.
- Length is never the goal. A long commit message is correct only when the
  reasoning genuinely needs the length; padding it is the same failure as a
  comment that restates the code.

```csharp
// Bad — 39 words for one fact.
// We are using a HashSet here instead of a List. The reason for this is that
// the lookup below runs for every row in the batch, and with a List that
// lookup would be O(n), which was too slow.

// Good — 12 words.
// HashSet: the lookup runs per row and List made the batch O(n^2).
```

## Do not delete a comment you cannot explain

This standard raises the bar for comments you write. It is not a licence to
strip comments from existing code.

- A comment that explains **why** stays, even when worded poorly.
- A comment whose purpose you cannot determine stays. It is load-bearing until
  proven otherwise.
- Delete only a comment that restates code, and only in code you are already
  changing. Do not sweep a file or a project for comments to remove.
- A comment that is wrong rather than redundant is a documentation accuracy
  finding. Fix the claim; do not silently delete it.

## TODO and HACK

Include the ticket. A `// TODO` with no ticket is noise, because nothing will
ever bring a reader back to it.

```csharp
// Bad
// TODO: handle the null case

// Good
// TODO ISFS-5210: remove once the legacy feed is retired.
```

## Commit messages, pull requests, and markdown

Both rules apply. Prose that restates what the reader can see is noise, and a
long paragraph carrying one fact is noise around a fact.

- **Commit message.** State why the change was made, and any consequence a
  reader cannot get from the diff — a required deployment order, a data
  migration, a rejected alternative. Do not list the files or methods you
  touched.
- **Pull request description.** State scope, risk, and what was verified. Do
  not paste a summary of the diff.
- **Markdown, README, and specification documents.** Document the decision, the
  constraint, and the thing that will surprise the next reader. Do not restate
  a signature, an enum's members, or a configuration key whose name already
  says what it does. A code block that duplicates source will drift from it.

```text
Bad:  Updated FilmService.cs and FilmRepository.cs. Added GetActiveFilmsAsync
      to FilmService and a new query to FilmRepository.

Good: Filter inactive films at the database instead of in the service. The
      studio page was loading the full catalog to discard most of it, which
      timed out for the largest studios.
```
