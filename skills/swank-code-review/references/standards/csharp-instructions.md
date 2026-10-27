---
description: >-
  Fetch when generating, reviewing, or modifying C# code in any .NET project.
  Contains Swank-specific conventions for solution folder layout (nested
  directories matching namespace segments, not dotted project names),
  project folder organization guidance (Repositories, Services, Models,
  Controllers) for larger projects, naming,
  file-scoped namespaces,
  var usage, guard clauses,
  collection expressions, LINQ fluent syntax,
  async/await and CancellationToken patterns, exception handling,
  dependency injection, structured logging with ILogger<T>, and XML
  documentation requirements.
---

# C# Coding Standards

## Namespaces and File Structure

- Always use file-scoped namespaces.
- File names must match class names. Do not place multiple classes in one file.
- Remove unused `using` directives.
- Ensure files conform to "ReSharper Green" best practices.

```csharp
// Do
namespace Swank.Films.Services;

public class FilmService
{
}

// Do not
namespace Swank.Films.Services
{
    public class FilmService
    {
    }
}
```

## Solution Folder Organization

When adding a project to a solution, the project's folder on disk must mirror its namespace segments as nested directories. Do not use the dotted project name as a single flat folder.

For a project named `AIInstructions.Web.Tests.csproj`, place it at `AIInstructions/Web/Tests/AIInstructions.Web.Tests.csproj`. Solution Explorer's solution folders should follow the same nesting.

```
// Do: Nested folders matching namespace segments
SolutionRoot/
├── AIInstructions/
│   ├── Web/
│   │   ├── Tests/
│   │   │   └── AIInstructions.Web.Tests.csproj
│   │   └── AIInstructions.Web.csproj
│   └── AIInstructions.csproj
└── AIInstructions.sln

// Do not: Flat folders named after the dotted project name
SolutionRoot/
├── AIInstructions/
│   └── AIInstructions.csproj
├── AIInstructions.Web/
│   └── AIInstructions.Web.csproj
├── AIInstructions.Web.Tests/
│   └── AIInstructions.Web.Tests.csproj
└── AIInstructions.sln
```

## Project Folder Organization

This is guidance, not a hard rule. Small projects — a handful of files, a quick console app, a thin library — are fine flat. Once a project grows past that point and files start accumulating in the root, organize them into folders by responsibility.

When that threshold is crossed, the conventional folders are:

- `Controllers/` — ASP.NET controllers (e.g., `OrderController`, `FilmController`).
- `Repositories/` — Repository interfaces and implementations (e.g., `IOrderRepository`, `OrderRepository`).
- `Services/` — Service interfaces and implementations (e.g., `IFilmService`, `FilmService`).
- `Models/` — Domain models, DTOs, and request/response types.

Add other folders as the project calls for them (e.g., `Extensions/`, `Mapping/`, `Configuration/`). None of these are required — deviate when it makes sense for the project.

Namespaces must align with whatever folder structure is used.

```
// Do: Files organized by responsibility once the project has grown
MyApplication/
├── Controllers/
│   └── OrderController.cs           // namespace MyApplication.Controllers
├── Models/
│   ├── Order.cs                     // namespace MyApplication.Models
│   └── OrderStatus.cs               // namespace MyApplication.Models
├── Repositories/
│   ├── IOrderRepository.cs          // namespace MyApplication.Repositories
│   └── OrderRepository.cs           // namespace MyApplication.Repositories
├── Services/
│   ├── IOrderService.cs             // namespace MyApplication.Services
│   └── OrderService.cs              // namespace MyApplication.Services
├── appsettings.json
└── Program.cs

// Do not: Everything in the project root once the file count has grown
MyApplication/
├── IOrderRepository.cs
├── IOrderService.cs
├── Order.cs
├── OrderController.cs
├── OrderRepository.cs
├── OrderService.cs
├── OrderStatus.cs
├── appsettings.json
└── Program.cs
```

## Naming Conventions

- Use `Id` in PascalCase and `id` in camelCase. Not `ID` or `iD`.
- Use PascalCase for classes, methods, properties, enums, and constants.
- Use camelCase for local variables and method parameters.
- Use camelCase with an underscore prefix (`_`) for private fields.
- Include explicit access modifiers on all members.
- Name methods with a verb-object structure (e.g., `ShowDialog()`, `UpdateLastModifiedDate()`).
- Suffix async methods with `Async` (except WPF/WinForms event handlers).
- Prefix interfaces with `I`. Name them using nouns, noun phrases, or adjectives.
- Default implementations should match the interface name (e.g., `DefaultTranscodeProcessor` for `ITranscodeProcessor`).
- Suffix custom attribute classes with `Attribute`.
- Suffix custom exception classes with `Exception`.
- Avoid public fields. Use properties instead.

```csharp
public class FilmService : IFilmService
{
    private readonly ILogger<FilmService> _logger;
    private int _processedCount;

    public FilmService(ILogger<FilmService> logger)
    {
        ArgumentNullException.ThrowIfNull(logger);
        _logger = logger;
    }

    public int ProcessedCount => _processedCount;

    public async Task<Film> GetFilmByIdAsync(
        int filmId,
        CancellationToken cancellationToken = default)
    {
        // ...
    }
}
```

## Type Declarations

- Use C# aliases (`int`, `string`, `bool`) rather than .NET types (`Int32`, `String`, `Boolean`).
- Do not use primary constructors on non-record classes. If existing code uses them, do not flag it during review.
- Default to classes and structs. Use records when the use case specifically calls for value equality semantics or immutable data transfer objects.
- Nullable reference types are configured project-by-project. Follow whatever the project has set.
- New C# projects should be created with nullability enabled and nullable warnings as errors.
  - `<Nullable>enable</Nullable>`
  - `<WarningsAsErrors>Nullable</WarningsAsErrors>`

## Properties

- On c# 11 or higher, use `required` on all required properties, including value types.

```csharp
// C# 11 or higher
public class ContentDetail
{
    public required int ContentDetailId { get; init; }
    public required string ContentPath { get; init; }
}

// Lower than C# 11
public class ContentDetail
{
    public int ContentDetailId { get; set; }
    public string ContentPath { get; set; } = string.Empty;
}
```

## `var` Usage

- Use `var` only when the type is obvious from the right side of the assignment.
- Do not use `var` when the type is ambiguous.

```csharp
// Fine, type is obvious
var count = 25;
var name = "Hello World!";
var films = new List<Film>();

// Do not use var, type is ambiguous
FilmResult result = service.ProcessFilmNumber(filmNumber);
JobDetail detail = service.GetNextJobDetail();
```

## Braces and Formatting

- Opening curly braces `{` go on a new line (Allman style).

## Readability

- Prefer readability over conciseness. One line of code might be elegant, but if it is confusing, split it into multiple statements.

```csharp
// Do
Film? film = await _filmRepository.GetByIdAsync(filmId, cancellationToken);
ArgumentNullException.ThrowIfNull(film);

string normalizedTitle = film.Title.Trim().ToLowerInvariant();
bool isFeatured = featuredTitles.Contains(normalizedTitle);

// Do not
bool isFeatured = featuredTitles.Contains(
    (await _filmRepository.GetByIdAsync(filmId, cancellationToken)
        ?? throw new ArgumentNullException(nameof(filmId)))
    .Title.Trim().ToLowerInvariant());
```

## Guard Clauses

- Public methods must null-check reference parameters and null-or-whitespace-check string parameters at the top of the body. Favor the same checks on private methods; omit only when every caller is trusted to pass valid values.
- Use the static `ThrowIf` guard methods (`ArgumentNullException.ThrowIfNull`, `ArgumentException.ThrowIfNullOrWhiteSpace`, etc.) rather than hand-rolled `if`/`throw` blocks.

```csharp
// Do
public void UpdateFilm(Film film, string title)
{
    ArgumentNullException.ThrowIfNull(film);
    ArgumentException.ThrowIfNullOrWhiteSpace(title);
    // ...
}

// Do not
public void UpdateFilm(Film film, string title)
{
    if (film is null) throw new ArgumentNullException(nameof(film));
    if (string.IsNullOrWhiteSpace(title)) throw new ArgumentException("...", nameof(title));
    // ...
}
```

## Strings

- Use `string.Empty` instead of `""`.
- String interpolation is preferred over `String.Format`.
- Use verbatim strings (`@""`) for multiline content.
- Prefer `StringBuilder` for long or repeated string manipulations.

```csharp
// Do
string message = $"Film {filmId} was processed by {userName}.";
string query = @"
    SELECT FilmId, Title
    FROM Films
    WHERE IsActive = 1";
```

## Collections and LINQ

- Use generic collections (`List<T>`, `Dictionary<TKey, TValue>`) over non-generic ones (`ArrayList`, `Hashtable`).
- Use collection expressions where applicable.
- Prefer fluent method syntax for LINQ queries over query syntax.
- Do not reflexively convert a `foreach` loop into a LINQ query — sometimes the loop is clearer.

```csharp
// Collection expressions
int[] ids = [1, 2, 3];
List<string> names = ["Alice", "Bob", "Charlie"];

// Fluent LINQ
List<Film> activeFilms = films
    .Where(film => film.IsActive)
    .OrderBy(film => film.Title)
    .ToList();

// Do not use query syntax
var activeFilms = from film in films
                  where film.IsActive
                  orderby film.Title
                  select film;
```

## Async/Await and CancellationToken

- Always use `async`/`await`. Never use `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()`. There are no exceptions to this rule.
- Always accept a `CancellationToken` parameter on async methods.
- `CancellationToken` must be the last parameter and default to `default`.
- Pass the token through to every async call in the chain.

```csharp
public async Task<IReadOnlyList<Film>> GetActiveFilmsAsync(
    int studioId,
    CancellationToken cancellationToken = default)
{
    Studio studio = await _studioRepository.GetByIdAsync(studioId, cancellationToken);
    ArgumentNullException.ThrowIfNull(studio);

    return await _filmRepository.GetByStudioAsync(studio.Id, cancellationToken);
}
```

## Exception Handling

- Avoid empty `catch` blocks. If truly necessary, document the justification.
- Catch specific exception types where possible.
- Use `throw;` to re-throw, never `throw exception;`.
- Prefer standard .NET exception types. Use the most specific applicable type.

```csharp
try
{
    await ProcessFilmAsync(filmId, cancellationToken);
}
catch (HttpRequestException exception)
{
    _logger.LogError(exception, "Failed to process film {FilmId}.", filmId);
    throw;
}
```

## Dependency Injection

- Use constructor injection as the default.

```csharp
// Do: Constructor injection
public class FilmService : IFilmService
{
    private readonly IFilmRepository _filmRepository;
    private readonly ILogger<FilmService> _logger;

    public FilmService(IFilmRepository filmRepository, ILogger<FilmService> logger)
    {
        ArgumentNullException.ThrowIfNull(filmRepository);
        ArgumentNullException.ThrowIfNull(logger);

        _filmRepository = filmRepository;
        _logger = logger;
    }
}
```

## Logging

- Use `Microsoft.Extensions.Logging.ILogger<T>` injected via DI.
- Always use structured logging with message templates. Never use string concatenation or interpolation in log messages.
- Use PascalCase for template property names.

```csharp
// Do
_logger.LogInformation("Processing film {FilmId} for studio {StudioName}.", filmId, studioName);
_logger.LogWarning("Film {FilmId} not found in catalog.", filmId);

// Do not
_logger.LogInformation($"Processing film {filmId} for studio {studioName}.");
_logger.LogInformation("Processing film " + filmId + " for studio " + studioName + ".");
```

## XML Documentation

- Document all non-private types, methods, properties, constructors, fields, events, and delegates.
- In an inheritance hierarchy, use `<inheritdoc />` instead of repeating documentation.
- Use `<see cref="..." />` to reference other types or members.

### Properties

```csharp
/// <summary>
/// The unique identifier of the film.
/// </summary>
public required int FilmId { get; init; }

/// <summary>
/// The title of the film.
/// </summary>
public required string Title { get; init; }
```

### Constructors

```csharp
/// <summary>
/// Creates a new instance of the <see cref="FilmService"/> class.
/// </summary>
/// <param name="filmRepository">The film repository.</param>
/// <param name="logger">The logger.</param>
public FilmService(IFilmRepository filmRepository, ILogger<FilmService> logger)
{
    ArgumentNullException.ThrowIfNull(filmRepository);
    ArgumentNullException.ThrowIfNull(logger);

    _filmRepository = filmRepository;
    _logger = logger;
}
```

### Methods

```csharp
/// <summary>
/// Retrieves all active films for the specified studio.
/// </summary>
/// <param name="studioId">The studio ID.</param>
/// <param name="cancellationToken">
/// A cancellation token to monitor for cancellation requests.
/// </param>
/// <returns>A read-only list of active films belonging to the studio.</returns>
/// <exception cref="ArgumentNullException">
/// Thrown if the studio with the specified <paramref name="studioId"/> does not exist.
/// </exception>
public async Task<IReadOnlyList<Film>> GetActiveFilmsAsync(
    int studioId,
    CancellationToken cancellationToken = default)
{
    // ...
}
```
