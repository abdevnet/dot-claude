---
description: >-
  Fetch when generating, reviewing, or modifying console applications, CRON
  jobs, scheduled tasks, Windows services, or single-run background processes
  in any .NET project. Contains Swank-specific conventions for the
  Swank.Applications.Console and Swank.Applications.WindowsServices NuGet
  packages, SingleRunConsoleApplication, WindowsServiceApplication,
  IApplicationService, configuration, Serilog logging, OpenTelemetry setup,
  SingleRunConsoleApplicationOptions, WindowsServiceApplicationOptions,
  and graceful shutdown patterns. When appsettings files are added or modified,
  also apply the csproj nesting rule from csharp-instructions.md.
---

# Console Application Standards

## SingleRunConsoleApplication

Use `SingleRunConsoleApplication<TService>` for console applications that run once and exit. This covers CRON jobs, scheduled tasks, and one-off operations. The class is provided by the `Swank.Applications.Console` NuGet package in the `Swank.Applications.Console.SingleRun` namespace.

`SingleRunConsoleApplication` provides the following out of the box:

- Configuration sources: `appsettings.json`, `appsettings.{environment}.json`, `secrets/appsettings.secrets.json`, environment variables
- Serilog logging with Swank defaults (Azure Log Analytics, console, file in Development)
- OpenTelemetry tracing, metrics, and logging (disabled by default, enabled via configuration)
- Graceful shutdown and error handling (sets `Environment.ExitCode = 1` on unhandled exceptions)
- Environment detection from `DOTNET_ENVIRONMENT`

## IApplicationService

Every `SingleRunConsoleApplication` and `WindowsServiceApplication` requires an `IApplicationService` implementation. The interface lives in the `Swank.Applications.Console` namespace. It has a single method that encapsulates all the work the application performs.

```csharp
namespace Swank.Applications.Console;

public interface IApplicationService
{
    Task ExecuteAsync(CancellationToken cancellationToken = default);
}
```

Implement this interface with your application's logic:

```csharp
using Swank.Applications.Console;

public class OrderSyncService : IApplicationService
{
    private readonly IOrderRepository _orderRepository;
    private readonly ILogger<OrderSyncService> _logger;

    public OrderSyncService(IOrderRepository orderRepository,
        ILogger<OrderSyncService> logger)
    {
        _orderRepository = orderRepository;
        _logger = logger;
    }

    public async Task ExecuteAsync(CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Starting order sync");

        // Application work goes here

        _logger.LogInformation("Order sync complete");
    }
}
```

## Basic Setup

Create the application in `Program.Main`, register services, and call `RunAsync`:

```csharp
using Swank.Applications.Console.SingleRun;

SingleRunConsoleApplication<OrderSyncService> app = new(
    applicationName: "Order Sync",
    registerApplicationServiceBindings: (context, serviceCollection) =>
    {
        string connectionString = context.Configuration.GetConnectionString("SGC")
            ?? throw new InvalidOperationException("Missing connection string: SGC");

        serviceCollection.AddSingleton<ISgcConnectionWrapperFactory>(
            new SgcConnectionWrapperFactory(connectionString));
        serviceCollection.AddSingleton<IOrderRepository, OrderRepository>();
        serviceCollection.AddSingleton<IApplicationService, OrderSyncService>();
    },
    options: null);

await app.RunAsync();
```

The `registerApplicationServiceBindings` delegate must register an `IApplicationService`. The application will throw `InvalidOperationException` at startup if this registration is missing.

The `HostBuilderContext` passed to the delegate provides access to `context.Configuration` for reading connection strings and other settings at registration time.

## WindowsServiceApplication

Use `WindowsServiceApplication<TService>` when deploying an application as a Windows service. The class is provided by the `Swank.Applications.WindowsServices` NuGet package in the `Swank.Applications.WindowsServices` namespace.

`WindowsServiceApplication` inherits from `SingleRunConsoleApplication` and adds `UseWindowsService()` to the host builder automatically. The same `IApplicationService` contract, configuration sources, logging, OpenTelemetry, and shutdown behavior all apply. The only difference is the type name and options type.

```csharp
// The setup is identical to SingleRunConsoleApplication, just swap the type
using Swank.Applications.WindowsServices;

WindowsServiceApplication<OrderSyncService> app = new(
    applicationName: "Order Sync",
    registerApplicationServiceBindings: (context, serviceCollection) =>
    {
        string connectionString = context.Configuration.GetConnectionString("SGC")
            ?? throw new InvalidOperationException("Missing connection string: SGC");

        serviceCollection.AddSingleton<ISgcConnectionWrapperFactory>(
            new SgcConnectionWrapperFactory(connectionString));
        serviceCollection.AddSingleton<IOrderRepository, OrderRepository>();
        serviceCollection.AddSingleton<IApplicationService, OrderSyncService>();
    });
```

Use `WindowsServiceApplicationOptions` instead of `SingleRunConsoleApplicationOptions`. It extends `SingleRunConsoleApplicationOptions`, so all the same delegate properties are available.

## SingleRunConsoleApplicationOptions

Pass `SingleRunConsoleApplicationOptions` to customize behavior. The options parameter is nullable and defaults are applied when omitted.

### Extending Default Configuration

Use `+=` on delegate properties to add to the defaults without replacing them.

```csharp
// Do: Use += to extend
SingleRunConsoleApplicationOptions options = new();

options.AddSerilogConfiguration += (context, logging) =>
{
    logging.WriteTo.File("additional-log.txt");
};

options.AddOpenTelemetryServices += (services, configuration, environment) =>
{
    // Additional OpenTelemetry instrumentation
};

SingleRunConsoleApplication<OrderSyncService> app = new(
    applicationName: "Order Sync",
    registerApplicationServiceBindings: (context, serviceCollection) =>
    {
        serviceCollection.AddSingleton<IApplicationService, OrderSyncService>();
    },
    options: options);
```

```csharp
// Do not: Use = to override unless you intentionally want to replace all defaults
options.AddSerilogConfiguration = (context, logging) =>
{
    // This replaces all Swank Serilog defaults
};
```

### Overriding Configuration Sources

Override `ConfigureAppConfiguration` only when you need completely custom configuration sources.

```csharp
options.ConfigureAppConfiguration = (hostEnvironment, configurationBuilder) =>
{
    configurationBuilder.AddJsonFile("customsettings.json", optional: true, reloadOnChange: true);
};
```

### OnBeforeBuild

Use `OnBeforeBuild` to run custom code against the `IHostBuilder` just before `Build()` is called:

```csharp
options.OnBeforeBuild = (hostBuilder) =>
{
    // Custom host configuration
};
```

## OpenTelemetry in Deployed Environments

OpenTelemetry is registered but disabled by default. Enable it in deployed environments through configuration. Do not add OpenTelemetry setup code manually when using `SingleRunConsoleApplication` or `WindowsServiceApplication`.

```json
{
  "OpenTelemetry": {
    "Enabled": true,
    "Exporters": {
      "AzureMonitor": {
        "Enabled": true,
        "ConnectionString": "[your-connection-string]"
      }
    }
  }
}
```

## appsettings.json

Do not add Serilog configuration to `appsettings.json` when using `SingleRunConsoleApplication` or `WindowsServiceApplication`. The defaults are pre-configured. Only add Serilog entries if you need to override a specific default.

Do not add OpenTelemetry configuration unless you are enabling it or overriding specific values in a deployed environment.

## Error Handling and Shutdown

`SingleRunConsoleApplication` and `WindowsServiceApplication` manage the application lifetime automatically. Do not duplicate this behavior in application code.

- Do not call `Environment.Exit()` or manage the application lifetime manually.
- Do not set `Environment.ExitCode` manually. The framework sets it to `1` on unhandled exceptions.
- Do not add top-level try/catch blocks for shutdown purposes. The framework logs unhandled exceptions and flushes Serilog automatically.
- Do not handle `OperationCanceledException` for shutdown logging. The framework logs cancellations as informational.
