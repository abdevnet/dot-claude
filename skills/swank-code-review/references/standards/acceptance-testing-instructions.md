---
description: >-
  Fetch when generating, reviewing, or modifying acceptance tests in any Swank
  .NET project. Contains Swank-specific conventions for acceptance test solution
  organization, NUnit test structure, parallel execution, AcceptanceTestingStartup
  and AcceptanceTestsBase patterns, one-time setup with SetUpFixture, the
  Swank.AcceptanceTesting NuGet package, IAcceptanceTestingFileSystem for local
  and Azure Pipelines environments, naming conventions, and test-against-real-systems
  philosophy.
---

# Acceptance Testing Standards

## Core Rules

- Acceptance tests run against real databases, real CRON jobs, real APIs, and real file systems.
- Do not use mocks, substitutions, or shortcuts in acceptance tests.
- Use NUnit for all acceptance tests.

## Solution Organization

Maintain separate solutions for application code and acceptance tests:

- **Application code + unit tests:** `{ComponentName}.sln` (e.g., `SamsungLynk.sln`)
- **Acceptance tests:** `{ComponentName}.AcceptanceTests.sln` (e.g., `SamsungLynk.AcceptanceTests.sln`)

## Parallel Execution

Apply `[Parallelizable(ParallelScope.All)]` to every test fixture. Design each test with zero shared state with any other test.

```csharp
[TestFixture]
[Parallelizable(ParallelScope.All)]
public class JobCreatorAcceptanceTests : AcceptanceTestsBase
{
    [Test]
    public async Task WhenJobCandidateExists_NewJobIsCreated()
    {
        // Test code here
    }
}
```

## Startup and Dependency Injection

Build configuration and register services in a static `AcceptanceTestingStartup` class. This keeps DI setup in one place and allows both the test base class and the one-time setup fixture to share it.

```csharp
namespace Shipment.Fulfillment.AcceptanceTests;

public static class AcceptanceTestingStartup
{
    public static IConfiguration BuildConfiguration() =>
        new ConfigurationBuilder()
            .AddJsonFile("appsettings.QA.json")
            .AddEnvironmentVariables()
            .Build();

    public static IServiceProvider BuildServiceProvider(IConfiguration configuration)
    {
        string sgcConnectionString = configuration.GetConnectionString("SGC")
            ?? throw new InvalidOperationException("Connection string 'SGC' not found.");

        return new ServiceCollection()
            .AddLogging()
            .AddSingleton<ISgcConnectionWrapperFactory>(sp =>
                new SgcConnectionWrapperFactory(sgcConnectionString))
            .AddSingleton<AcceptanceTestingRepository>()
            .AddSingleton<AcceptanceTestingService>()
            .BuildServiceProvider();
    }
}
```

Use an abstract base class to resolve services and provide shared validation helpers. Each test fixture inherits from this base class.

```csharp
namespace Shipment.Fulfillment.AcceptanceTests;

public abstract class AcceptanceTestsBase
{
    protected readonly AcceptanceTestingService AcceptanceTestingService;

    protected AcceptanceTestsBase()
    {
        IConfiguration configuration = AcceptanceTestingStartup.BuildConfiguration();
        IServiceProvider services = AcceptanceTestingStartup.BuildServiceProvider(configuration);

        AcceptanceTestingService = services.GetRequiredService<AcceptanceTestingService>();
    }

    protected static void ValidateCreatedJob(ExpandedManufacturingJob createdJob,
        FulfillmentJobCandidate jobCandidate)
    {
        Assert.That(createdJob, Is.Not.Null);
        Assert.That(createdJob.Id, Is.GreaterThan(0));
        Assert.That(createdJob.Type, Is.EqualTo("Shipment Fulfillment"));
    }

    protected static void ValidateRejectedJob(ExpandedManufacturingJob rejectedJob,
        int expectedJobId)
    {
        Assert.That(rejectedJob, Is.Not.Null);
        Assert.That(rejectedJob.Id, Is.EqualTo(expectedJobId));
        Assert.That(rejectedJob.Status, Is.EqualTo(JobStatusNames.Rejected));

        foreach (ExpandedManufacturingTask task in rejectedJob.Tasks)
        {
            Assert.That(task.Status, Is.EqualTo(TaskStatusNames.Rejected));
        }
    }
}
```

## One-Time Setup

Use NUnit's `[SetUpFixture]` for assembly-wide one-time setup. Place the class in no namespace so it applies to the entire assembly. Do not use manual locking or static flags for one-time initialization.

```csharp
using NUnit.Framework;

[SetUpFixture]
#pragma warning disable CA1050 // Declare types in namespaces
public sealed class AcceptanceTestingRunHooks
#pragma warning restore CA1050 // Declare types in namespaces
{
    private readonly IManufacturingTestingRepository _repository;

    public AcceptanceTestingRunHooks()
    {
        IConfiguration configuration = AcceptanceTestingStartup.BuildConfiguration();
        IServiceProvider services = AcceptanceTestingStartup.BuildServiceProvider(configuration);

        _repository = services.GetRequiredService<IManufacturingTestingRepository>();
    }

    [OneTimeSetUp]
    public Task OneTimeSetUpAsync() =>
        _repository.RejectAllActiveJobsAsync(jobType: "Shipment Fulfillment");
}
```

## Naming Conventions

### Projects

Name acceptance test projects as `{ComponentUnderTest}.AcceptanceTests.csproj`.

Examples: `SamsungLynk.AcceptanceTests.csproj`, `Shipment.Fulfillment.AcceptanceTests.csproj`, `MissingContent.AcceptanceTests.csproj`

### Test Classes

Name test classes based on the component they test, suffixed with `AcceptanceTests`.

Examples: `JobCreatorAcceptanceTests`, `JobRejecterAcceptanceTests`, `EncryptorAcceptanceTests`

### Test Methods

Follow the pattern `{Scenario}_{ExpectedOutcome}`.

Examples:

- `WhenJobCandidateExists_NewJobIsCreated`
- `WhenJobHasACancelledOrderLicense_JobIsRejected`
- `CompletedContentDetailSnapshotExistsInSnapshotData_CompletesEncryption`
- `MissingSnapshotData_ReleasesEncryptingTaskInError`

## Swank.AcceptanceTesting NuGet Package

Reference the `Swank.AcceptanceTesting` package for shared abstractions. Do not reference this package from non-acceptance-test projects.

```xml
<PackageReference Include="Swank.AcceptanceTesting" Version="[Latest Version]" />
```

The package includes a Roslyn analyzer (`Swank.AcceptanceTesting.Analyzers`) that reports a compiler warning if a project referencing the package does not contain "AcceptanceTests" in its name.

### IAcceptanceTestingFileSystem

The `IAcceptanceTestingFileSystem` interface provides file system operations that work across local development and Azure Pipelines environments.

Register it via the extension method:

```csharp
services.AddAcceptanceTestingFileSystem(configuration);
```

The correct implementation is resolved automatically based on the runtime environment:

- **Local (developer machine):** `SystemIOAcceptanceTestingFileSystem`, which delegates to standard `System.IO` types.
- **Azure Pipelines:** `SMBLibraryAcceptanceTestingFileSystem`, which uses SMBLibrary to access file shares via SMB credentials.

All file and directory paths must use the Windows format with `\` separators, not `/`.

```csharp
// Do: Windows-formatted path
bool fileExists = fileSystem.FileExists("\\\\smpdev03\\FakeISILON\\TestAdebsDigitalLibrary\\0057285.ts");

// Do not: Forward slashes
bool fileExists = fileSystem.FileExists("//smpdev03/FakeISILON/TestAdebsDigitalLibrary/0057285.ts");
```

### MediaFileInfoAssertions

The `MediaFileInfoAssertions` class provides static methods for validating MediaFileInfo manifests in both JSON and XML formats.

```csharp
MediaFileInfoAssertions.ValidateMediaFileInfoJson(jsonManifestBytes,
    expectedArcProductNumber,
    expectedVersionCode,
    expectedEncryptedFileName);

MediaFileInfoAssertions.ValidateMediaFileInfoXml(xmlManifestBytes,
    expectedArcProductNumber,
    expectedVersionCode,
    expectedEncryptedFileName);
```

## Azure Pipelines

Acceptance tests run in Azure Pipelines with manual triggers. The `ado-auto-test` variable group provides `SMB_USERNAME` and `SMB_PASSWORD` credentials for file system access. Reference this variable group in pipeline YAML and pass the credentials as environment variables to the test task.

Pipeline configuration for SMB file system access is documented on Confluence:

- [How to Access File Systems in Acceptance Tests Running in Azure Pipelines](https://swankmp.atlassian.net/wiki/x/BgB5zQ)

## Test Structure

```csharp
[TestFixture]
[Parallelizable(ParallelScope.All)]
public class EncryptorAcceptanceTests : AcceptanceTestsBase
{
    [Test]
    public async Task CompletedContentDetailSnapshotExistsInSnapshotData_CompletesEncryption()
    {
        // Put the database into the required state for this scenario.
        // Set up any other real dependencies required for this scenario.

        // Perform the action the scenario is testing.
        // Examples: wait for a CRON job to execute, call an API.

        // Validate the output of the action.
        // Examples: check the database, assert over an API response,
        // check a file system for created files.
    }

    [TestCase(3, "0067997", "CC", true)]
    [TestCase(4, "0074948", "WS", false)]
    public async Task CompletedContentDetailSnapshotExistsInSnapshotData_CompletesEncryption(
        int arcLineNumber,
        string arcProductNumber,
        string orderedVersionCode,
        bool writeOnlyJsonManifest)
    {
        // Use parameterized tests when the same scenario applies to
        // multiple input variations.
    }
}
```
