# Standards Selection

Every file in `standards/` is a verbatim copy of a document from the Swank AI
Instructions catalog (`~/projects/ai-instructions`, under
`AIInstructions/AIInstructions.Web/Documents/`). The catalog ID is the source
path without the extension. Run `scripts/sync-standards.sh` to refresh the copies.

Each file keeps its YAML front matter. The `description` field is the catalog's
own "fetch when" rule and wins if this table and the front matter disagree.

Match on what the code does, not on the extension alone. The whole catalog is
about 48k tokens; load a document whenever its signal might apply.

## Workflow documents

| File | Catalog ID | Role |
|---|---|---|
| code-review-instructions.md | review/code-review-instructions | The review workflow: change set, precedence, severity, gate, report format. Read first. |
| code-review-lenses-instructions.md | review/code-review-lenses-instructions | The 35 lenses. Always loaded. |
| comments-instructions.md | code/comments-instructions | Comments, commit messages, PR descriptions, markdown. Always loaded. |
| documentation-accuracy-instructions.md | review/documentation-accuracy-instructions | The required documentation accuracy pass. |

## By file type

| Signal | File | Catalog ID |
|---|---|---|
| `.cs` | csharp-instructions.md | code/csharp-instructions |
| `.ts`, `.html`, `.scss` in an Angular project | angular-instructions.md | code/angular-instructions |
| `.sql`, or SQL embedded in another language (below) | sqlserver-instructions.md | database/sqlserver-instructions |
| `*.spec.ts` | angular-testing-instructions.md, with angular-instructions.md | testing/angular-testing-instructions |
| `*Tests.cs`, `*Test.cs`, path contains `.Tests/` or `/Tests/`, `[TestFixture]`, `[Test]`, `NSubstitute`, `Assert.That` | csharp-testing-instructions.md, with csharp-instructions.md | testing/csharp-testing-instructions |
| Path contains `AcceptanceTests`; `Swank.AcceptanceTesting`, `AcceptanceTestsBase`, `AcceptanceTestingStartup` | acceptance-testing-instructions.md instead of csharp-testing-instructions.md | testing/acceptance-testing-instructions |
| `appsettings*.json` added or modified | csharp-instructions.md (csproj nesting rule) plus the area document for the project type | |

## By what C# code does

Load in addition to csharp-instructions.md when any signal appears in the changed code or paths.

| Signal | File | Catalog ID |
|---|---|---|
| `SwankWebApplication`, `WebApplication`, `[ApiController]`, `Map*` endpoint groups, `IEndpointRouteBuilder`, middleware, `ProblemDetails`, `HybridCache`, `AddAuthentication`, `Program.cs` in a web project | aspnetcore-instructions.md | code/aspnetcore-instructions |
| `HttpClient`, `IHttpClientFactory`, `AddHttpClient`, `Swank.Web.Client`, `SwankHttpStandardResilienceOptions`, `DelegatingHandler`, `PolicyConfiguration` | httpclient-instructions.md | code/httpclient-instructions |
| `SingleRunConsoleApplication`, `WindowsServiceApplication`, `IApplicationService`, `Swank.Applications.Console`, `Swank.Applications.WindowsServices`, `IHostedService` or `BackgroundService` in a console or service project | console-application-instructions.md | code/console-application-instructions |
| Path or type name contains `Repository`, `DataAccess`, `Dal`; `IDbConnectionWrapperFactory`, `IDbConnectionWrapper`, `Swank.Data`, Dapper calls, `DbContext`, connection strings | data-instructions.md, plus sqlserver-instructions.md when SQL text is present | database/data-instructions |
| `SwankResult`, `SwankResult<` | swankresult-instructions.md | code/swankresult-instructions |
| `IProductPublicityService`, `ProductPublicityService`, `ProductPublicityApi` namespace or appsettings section | productpublicityapi-instructions.md | code/productpublicityapi-instructions |

## Embedded SQL

Repository and data-access code carries SQL even when the file is C# or Java.
Treat the SQL text as SQL Server and load sqlserver-instructions.md when you see:

- string literals containing SELECT, INSERT, UPDATE, DELETE, FROM, WHERE, MERGE
- Dapper: `QueryAsync<T>("SELECT ...")`, `ExecuteAsync("INSERT ...")`
- ADO.NET: `SqlCommand`, `cmd.CommandText = "..."`
- Entity Framework raw SQL: `FromSqlRaw()`, `ExecuteSqlRaw()`
- JDBC: `executeQuery("...")`, `executeUpdate("...")`

Review the SQL for schema prefixes, parameterization, bracketing, naming and
data types, not just the C# around it. Injection risk and query quality do not
go away because the query is a string.
