---
description: >-
  Fetch when generating, reviewing, or modifying C# unit tests, NUnit test
  fixtures, NSubstitute mocks, or test assertions in any .NET project. Contains
  Swank-specific conventions for NUnit as the test framework, NSubstitute for
  mocking, Assert.That assertion style, test setup with [SetUp], test naming
  patterns, Dapper repository testing with SQL and parameter validation,
  and the Swank.Tests NuGet package helpers.
---

# C# Unit Testing Standards

## Test Framework

- Use NUnit as the test framework. Do not use xUnit or MSTest.
- Use NSubstitute for mocking by default. Some legacy projects use Moq, which is acceptable when requested. Do not use FakeItEasy.
- Use plain `Assert.That` for assertions. Do not use FluentAssertions or Shouldly.
- Use `// Arrange`, `// Act`, `// Assert` comments.

## Test Structure

```csharp
[TestFixture]
public class FilmServiceTests
{
    private IFilmRepository _filmRepository;
    private ILogger<FilmService> _logger;
    private FilmService _filmService;

    [SetUp]
    public void SetUp()
    {
        _filmRepository = Substitute.For<IFilmRepository>();
        _logger = Substitute.For<ILogger<FilmService>>();
        _filmService = new FilmService(_filmRepository, _logger);
    }

    [Test]
    public async Task GetActiveFilmsAsync_WhenStudioExists_ReturnsFilms()
    {
        List<Film> expectedFilms = [new Film { Id = 1, Title = "Test Film" }];
        _filmRepository.GetByStudioAsync(5, Arg.Any<CancellationToken>())
            .Returns(expectedFilms);

        IReadOnlyList<Film> result = await _filmService.GetActiveFilmsAsync(5);

        Assert.That(result, Has.Count.EqualTo(1));
        Assert.That(result[0].Title, Is.EqualTo("Test Film"));
    }
}
```

## Naming

- Name test classes as `{ClassUnderTest}Tests` (e.g., `FilmServiceTests`).
- Name test methods as `{Method}_{Scenario}_{ExpectedResult}` (e.g., `GetActiveFilmsAsync_WhenStudioExists_ReturnsFilms`).

## Setup

- Use `[SetUp]` to create substitutes and construct the system under test.
- Store substitutes as fields so they are accessible in both setup and test methods.
- Reconstruct everything per test via `[SetUp]`. Do not share state across tests.

## Mocking with NSubstitute

- Use `Substitute.For<T>()` to create mocks.
- Use `.Returns()` to configure return values.
- Use `Arg.Any<T>()` when the exact argument value is not relevant to the test.
- Use `.Received()` and `.DidNotReceive()` to verify calls when the test is about side effects rather than return values.

```csharp
// Configure a return value
_filmRepository.GetByStudioAsync(5, Arg.Any<CancellationToken>())
    .Returns(expectedFilms);

// Verify a call was made
await _filmRepository.Received(1).DeleteAsync(filmId, Arg.Any<CancellationToken>());

// Verify a call was not made
await _filmRepository.DidNotReceive().DeleteAsync(Arg.Any<int>(), Arg.Any<CancellationToken>());
```

## Assertions

- Use NUnit's constraint model (`Assert.That` with `Is.*` and `Has.*`).
- Do not use the classic model (`Assert.AreEqual`, `Assert.IsTrue`).

```csharp
// Do
Assert.That(result, Is.Not.Null);
Assert.That(result.Title, Is.EqualTo("Test Film"));
Assert.That(result, Has.Count.EqualTo(3));
Assert.That(result.IsActive, Is.True);

// Do not
Assert.IsNotNull(result);
Assert.AreEqual("Test Film", result.Title);
Assert.IsTrue(result.IsActive);
```

## Async Tests

- Use `async Task` as the test method return type. Do not use `async void`.
- Use `CancellationToken.None` or `Arg.Any<CancellationToken>()` as appropriate.

```csharp
// Do
[Test]
public async Task GetFilmAsync_WhenFilmExists_ReturnsFilm()
{
    _filmRepository.GetByIdAsync(1, Arg.Any<CancellationToken>())
        .Returns(new Film { Id = 1 });

    Film result = await _filmService.GetFilmByIdAsync(1, CancellationToken.None);

    Assert.That(result, Is.Not.Null);
}

// Do not
[Test]
public async void GetFilmAsync_WhenFilmExists_ReturnsFilm()
{
    // async void tests may not be awaited by the runner
}
```

## Exception Testing

Use `Assert.ThrowsAsync<T>` or `Assert.That` with `Throws` constraints to verify exceptions.

```csharp
[Test]
public void UpdateFilm_WhenFilmIsNull_ThrowsArgumentNullException()
{
    Assert.That(() => _filmService.UpdateFilm(null!, "Title"),
        Throws.TypeOf<ArgumentNullException>());
}
```

## Repository Testing

When testing Dapper repository methods, always verify the exact SQL string and parameter values passed to the `IDbConnectionWrapper`. An accidental SQL change must not go unnoticed.

### Setup

Mock `IDbConnectionWrapperFactory` and `IDbConnectionWrapper` in `[SetUp]`. Wire `CreateAsync()` to return the wrapper substitute.

```csharp
[TestFixture]
public class OrderRepositoryTests
{
    private ISgcConnectionWrapperFactory _sgcConnectionWrapperFactory;
    private IDbConnectionWrapper _sgcConnectionWrapper;
    private OrderRepository _orderRepository;

    [SetUp]
    public void SetUp()
    {
        _sgcConnectionWrapperFactory = Substitute.For<ISgcConnectionWrapperFactory>();
        _sgcConnectionWrapper = Substitute.For<IDbConnectionWrapper>();

        _sgcConnectionWrapperFactory.CreateAsync(Arg.Any<CancellationToken>())
            .Returns(_sgcConnectionWrapper);

        _orderRepository = new OrderRepository(_sgcConnectionWrapperFactory);
    }
}
```

### SQL Verification

Use `.Received()` with the exact SQL string the repository should execute. This catches unintentional query changes.

```csharp
[Test]
public async Task GetOrderAsync_ExecutesExpectedQuery()
{
    // Arrange
    int orderNumber = 12345;

    _sgcConnectionWrapper.QueryFirstOrDefaultAsync<Order>(
        Arg.Any<string>(), Arg.Any<object>())
        .Returns(new Order { OrderNumber = orderNumber });

    // Act
    await _orderRepository.GetOrderAsync(orderNumber, CancellationToken.None);

    // Assert
    await _sgcConnectionWrapper.Received(1).QueryFirstOrDefaultAsync<Order>(@"
            SELECT OrderNumber, CustomerNumber, Status, OrderEntryDate
            FROM ARC_OrderDetail
            WHERE OrderNumber = @OrderNumber",
        Arg.Any<object>());
}
```

### Parameter Validation

Verify that the anonymous parameter object passed to Dapper contains the expected values.

#### Swank.Tests Package (Preferred)

The `Swank.Tests` NuGet package provides extension methods for validating properties on anonymous objects. Use these when the project references the package.

```xml
<PackageReference Include="Swank.Tests" Version="[Latest Version]" />
```

Use `HasIntegerPropertyValue` and `HasStringPropertyValue` for common types:

```csharp
// Assert
await _sgcConnectionWrapper.Received(1).QueryFirstOrDefaultAsync<Order>(@"
        SELECT OrderNumber, CustomerNumber, Status, OrderEntryDate
        FROM ARC_OrderDetail
        WHERE OrderNumber = @OrderNumber",
    Arg.Is<object>(p =>
        p.HasIntegerPropertyValue("OrderNumber", orderNumber)));
```

For multiple parameters, chain with `&&`:

```csharp
Arg.Is<object>(p =>
    p.HasIntegerPropertyValue("OrderNumber", orderNumber)
    && p.HasStringPropertyValue("Status", "Active"))
```

For types beyond `int` and `string`, use the generic `HasPropertyValue<T>`:

```csharp
Arg.Is<object>(p =>
    p.HasPropertyValue("StartDate", expectedDate, (a, b) => a == b))
```

#### Without Swank.Tests (Fallback)

When the project does not reference `Swank.Tests`, use inline reflection:

```csharp
Arg.Is<object>(p =>
    p.GetType().GetProperty("OrderNumber")!
        .GetValue(p)!
        .Equals(orderNumber))
```
