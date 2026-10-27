---
description: >-
  Fetch when generating, reviewing, or modifying ASP.NET Core web APIs,
  services, or middleware in any .NET project. Contains Swank-specific
  conventions for SwankWebApplication, service registration, configuration
  patterns, authentication with Microsoft Entra ID, authorization, error
  handling with ProblemDetails, health checks, caching with HybridCache,
  OpenAPI/Swagger, Minimal API endpoint grouping, background services,
  response compression, and manual mapping. When appsettings files are
  added or modified, also apply the csproj nesting rule from
  csharp-instructions.md.
---

# ASP.NET Core Coding Standards

## SwankWebApplication

Use `SwankWebApplication.CreateBuilder` instead of `WebApplication.CreateBuilder` for new projects and refactors. This is encouraged but not required. If the user chooses not to use it, do not push back.

`SwankWebApplication.CreateBuilder` provides the following out of the box:

- Configuration sources: `appsettings.json`, `appsettings.{environment}.json`, `secrets/appsettings.secrets.json`, environment variables
- Serilog logging with Swank defaults (Azure Log Analytics, console, file in Development)
- OpenTelemetry tracing, metrics, and logging with health check instrumentation
- Environment detection from `ASPNETCORE_ENVIRONMENT`

The package is `Swank.Applications.Web`. The class lives in the `Swank.Applications.Web` namespace.

### Basic Usage

```csharp
// Do: Use SwankWebApplication for new projects
using Swank.Applications.Web;

WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args);

WebApplication app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { Status = "healthy" }));

await app.RunAsync();
```

```csharp
// Acceptable: Standard WebApplication.CreateBuilder if the team prefers
WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
```

### Passing Options

Pass `SwankWebApplicationOptions` to customize behavior. The options parameter is nullable and defaults are applied when omitted.

```csharp
WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args, options: null);
```

### Extending Default Configuration

Use `+=` on delegate properties to add to the defaults without replacing them.

```csharp
// Do: Use += to extend
SwankWebApplicationOptions options = new();

options.AddSerilogConfiguration += (context, logging) =>
{
    logging.WriteTo.File("additional-log.txt");
};

options.AddOpenTelemetryServices += (services, configuration, environment) =>
{
    // Additional OpenTelemetry instrumentation
};

WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args, options);
```

```csharp
// Don't: Use = to override unless you intentionally want to replace all defaults
options.AddSerilogConfiguration = (context, logging) =>
{
    // This replaces all Swank Serilog defaults
};
```

### Overriding Configuration Sources

Override `ConfigureAppConfiguration` only when you need completely custom configuration sources.

```csharp
SwankWebApplicationOptions options = new();

options.ConfigureAppConfiguration = (hostEnvironment, configurationBuilder) =>
{
    configurationBuilder.AddJsonFile("customsettings.json", optional: true, reloadOnChange: true);
};

WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args, options);
```

### OpenTelemetry in Deployed Environments

SwankWebApplication registers OpenTelemetry but disables it by default. Enable it in deployed environments through configuration. Do not add OpenTelemetry setup code manually when using SwankWebApplication.

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

### appsettings.json

When using SwankWebApplication, Serilog configuration does not need to appear in `appsettings.json`. The defaults are added in-memory by the framework. Only add Serilog entries to `appsettings.json` if you need to override a specific default.

Similarly, OpenTelemetry defaults are pre-configured. Only add the `OpenTelemetry` section to enable it or override specific values in deployed environments.

---

## Service Registration

### Configuration at Registration Time

Read configuration values during service registration and pass them as constructor parameters. Do not inject `IOptions<T>` or `IConfiguration` into services.

```csharp
// Do: Read config at registration, pass as constructor parameter
string connectionString = builder.Configuration.GetConnectionString("SGC")
    ?? throw new InvalidOperationException("Missing connection string: SGC");

builder.Services.AddTransient<ISgcConnectionFactory>(sp =>
    new SgcConnectionFactory(connectionString));
```

```csharp
// Do: Use factory lambdas to resolve dependencies and wire parameters
TimeSpan pollingInterval = TimeSpan.FromMinutes(
    builder.Configuration.GetValue("ChangeMonitor:PollingIntervalMinutes", defaultValue: 1));

builder.Services.AddHostedService(sp =>
    new ChangeMonitorService(
        sp.GetRequiredService<IRepository>(),
        pollingInterval,
        sp.GetRequiredService<ILogger<ChangeMonitorService>>()));
```

```csharp
// Do not: Inject IOptions<T> or IConfiguration into services
public class MyService
{
    public MyService(IOptions<MyOptions> options) { }
    public MyService(IConfiguration configuration) { }
}
```

If `IOptions<T>` is used during registration, unwrap the value with a factory so the service receives `T` directly:

```csharp
builder.Services.Configure<CachingOptions>(builder.Configuration.GetSection("Caching"));

builder.Services.AddSingleton(sp =>
    sp.GetRequiredService<IOptions<CachingOptions>>().Value);
```

### Program.cs Organization

Keep `Program.cs` focused on the application's startup sequence. Group related registrations and middleware together. When `Program.cs` grows beyond what is easy to scan, extract related concerns into extension methods on `WebApplicationBuilder` (for service registration) or `WebApplication` (for middleware). Treat both sides consistently: if registration is extracted, extract middleware configuration too.

Do not extract prematurely. A short `Program.cs` with inline registrations and middleware is fine.

```csharp
// Do: Short Program.cs with inline registration and middleware
WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args);

builder.Services.AddProblemDetails();
builder.Services.AddHealthChecks()
    .AddCheck("self", () => HealthCheckResult.Healthy());

WebApplication app = builder.Build();

app.UseExceptionHandler();
app.MapHealthChecks("/hc").AllowAnonymous();

await app.RunAsync();
```

```csharp
// Do: Extract both sides when Program.cs grows
WebApplicationBuilder builder = SwankWebApplication.CreateBuilder(args);

builder.AddServices();

WebApplication app = builder.Build();

app.ConfigureMiddleware();

await app.RunAsync();
```

```csharp
// Do not: Extract registration but leave a long middleware pipeline inline, or vice versa
```

---

## Authentication

### New and Refactored Applications

New applications and refactors should use JWT Bearer authentication with Microsoft Entra ID. Legacy applications may use an older bearer token flow, which is acceptable but should not be used for new work.

```csharp
builder.Services
    .AddAuthentication(defaultScheme: JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(jwt =>
    {
        jwt.Authority = $"https://login.microsoftonline.com/{tenantId}/v2.0";
        jwt.Audience = applicationId;
        jwt.MapInboundClaims = false;

        jwt.TokenValidationParameters.ValidateIssuer = true;
        jwt.TokenValidationParameters.ValidateAudience = true;
        jwt.TokenValidationParameters.ValidateLifetime = true;

        jwt.TokenValidationParameters.RoleClaimType = ClaimTypes.Role;

        jwt.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                if (context.Principal?.Identity is ClaimsIdentity identity)
                {
                    // Standardize NameIdentifier from the azp claim
                    Claim? azpClaim = context.Principal.Claims
                        .FirstOrDefault(c => c.Type == "azp");
                    if (azpClaim is not null)
                    {
                        identity.AddClaim(
                            new Claim(ClaimTypes.NameIdentifier, azpClaim.Value));
                    }

                    // Map Entra "roles" claims to ClaimTypes.Role
                    foreach (Claim roleClaim in context.Principal.Claims.Where(c => c.Type == "roles"))
                    {
                        identity.AddClaim(new Claim(ClaimTypes.Role, roleClaim.Value));
                    }
                }

                return Task.CompletedTask;
            },
        };
    });
```

Requirements for this pattern:

- Always set `MapInboundClaims = false` to preserve original claim names from the token.
- Always normalize claims in `OnTokenValidated` so `ClaimTypes.NameIdentifier` and `ClaimTypes.Role` are consistent regardless of token format.
- Always use the v2.0 authority endpoint. The Entra app registration must have `requestedAccessTokenVersion` set to `2` in the manifest.
- The `audience` must match the Application ID URI configured in Entra (typically `api://<client-id>`).

### Secure by Default

Configure `FallbackPolicy` so all endpoints require authentication unless explicitly opted out:

```csharp
builder.Services.AddAuthorization(options =>
{
    options.DefaultPolicy =
        new AuthorizationPolicyBuilder().RequireAuthenticatedUser().Build();

    options.FallbackPolicy = options.DefaultPolicy;
});
```

Individual endpoints opt out with `AllowAnonymous()`.

### Entra App Registration

When setting up Entra for an API:

- Create separate app registrations for Nonprod and Prod.
- Follow the naming convention: `{App Name} - Nonprod`, `{App Name} - Prod`.
- Define app roles for authorization (e.g., `myapi.read`, `myapi.write`). Use clear, stable role values that represent capabilities.
- Set `requestedAccessTokenVersion` to `2` in the manifest.
- No client secret is needed for the API itself. Client applications use their own credentials.

When setting up Entra for a client consuming an API:

- Create a client app registration with a client secret.
- Under API permissions, add the target API's app roles.
- Admin consent is required. Create an infrastructure ticket requesting consent.
- Tokens are acquired via the client credentials grant against the tenant v2.0 token endpoint.

---

## Error Handling

New and refactored applications should use ProblemDetails for error responses. Legacy applications may not follow this pattern.

```csharp
// Service registration
builder.Services.AddProblemDetails();

// Middleware pipeline
app.UseExceptionHandler();  // Converts unhandled exceptions to ProblemDetails
app.UseStatusCodePages();   // Writes ProblemDetails for 4xx/5xx without a body
```

For Minimal APIs, apply common error response metadata at the group level:

```csharp
RouteGroupBuilder apiGroup = app.MapGroup()
    .RequireAuthorization()
    .ProducesProblem(StatusCodes.Status400BadRequest)
    .ProducesProblem(StatusCodes.Status401Unauthorized)
    .ProducesProblem(StatusCodes.Status500InternalServerError);
```

---

## Health Checks

Include health checks in all applications. Use two endpoints:

```csharp
// /hc returns all checks
app.MapHealthChecks("/hc", new HealthCheckOptions
{
    Predicate = _ => true,
    ResponseWriter = UIResponseWriter.WriteHealthCheckUIResponse,
}).AllowAnonymous();

// /hc/ready returns only checks tagged "ready"
app.MapHealthChecks("/hc/ready", new HealthCheckOptions
{
    Predicate = r => r.Tags.Contains("ready"),
    ResponseWriter = UIResponseWriter.WriteHealthCheckUIResponse,
}).AllowAnonymous();
```

When registering health checks:

- Always include a basic self-check: `healthChecks.AddCheck("self", () => HealthCheckResult.Healthy());`
- Use `HealthStatus.Unhealthy` for critical dependencies (e.g., the primary database).
- Use `HealthStatus.Degraded` for non-critical dependencies (e.g., Redis cache).
- Tag dependency checks with `"ready"` so they appear in the readiness endpoint.

```csharp
IHealthChecksBuilder healthChecks = builder.Services.AddHealthChecks();

healthChecks.AddCheck("self", () => HealthCheckResult.Healthy());

healthChecks.AddSqlServer(
    connectionString: connectionString,
    name: "Primary Database",
    failureStatus: HealthStatus.Unhealthy,
    tags: ["ready"]);

healthChecks.AddRedis(
    redisConnectionString: redisConnectionString,
    name: "Redis",
    failureStatus: HealthStatus.Degraded,
    tags: ["ready"]);
```

Swank provides custom health check packages for SQL Server with failover support (`Swank.HealthChecks.SqlServer`) and Redis Sentinel (`Swank.HealthChecks.Redis`). Use these when the application connects to mirrored SQL Server instances or Redis Sentinel clusters.

---

## Caching

Use `HybridCache` for caching in new applications. Do not use `IMemoryCache` or `IDistributedCache` directly.

Register Redis conditionally based on configuration. Do not assume Redis is available.

```csharp
CachingOptions cachingOptions = builder.Configuration.GetCachingOptions();

if (cachingOptions.Redis.Enabled)
{
    ConfigurationOptions redisConfigurationOptions =
        builder.Configuration.BuildRedisConfigurationOptions();

    builder.Services.AddStackExchangeRedisCache(options =>
    {
        options.ConfigurationOptions = redisConfigurationOptions;
    });
}

builder.Services.AddHybridCache(options =>
{
    options.DefaultEntryOptions = new HybridCacheEntryOptions
    {
        Expiration = TimeSpan.FromMinutes(cachingOptions.DefaultExpirationMinutes),
        LocalCacheExpiration = null, // Derived automatically, never exceeds Expiration
    };
});
```

When Redis is not enabled, `HybridCache` falls back to in-memory caching only.

---

## OpenAPI and Swagger

Enable OpenAPI and Swagger UI in non-production environments. Do not enable Swagger in production.

```csharp
if (!app.Environment.IsProduction())
{
    app.MapOpenApi().AllowAnonymous();

    app.UseSwaggerUI(options =>
    {
        options.RoutePrefix = "swagger";
        options.SwaggerEndpoint(url: "/openapi/v1.json", name: "My API v1");
    });
}
```

---

## Minimal API Patterns

Group endpoints with `MapGroup()` and apply shared metadata at the group level.

```csharp
ApiVersionSet apiVersionSet = app.NewApiVersionSet("MyApi")
    .HasApiVersion(new ApiVersion(1, 0))
    .ReportApiVersions()
    .Build();

RouteGroupBuilder apiGroup = app.MapGroup()
    .RequireAuthorization()
    .WithApiVersionSet(apiVersionSet)
    .ProducesProblem(StatusCodes.Status400BadRequest)
    .ProducesProblem(StatusCodes.Status401Unauthorized)
    .ProducesProblem(StatusCodes.Status500InternalServerError);

RouteGroupBuilder v1 = apiGroup.MapGroup()
    .HasApiVersion(new ApiVersion(1, 0));
```

When adding versioning to an existing project, check the project's current versioning approach (header-based, URL segment, or query string) and match it. When creating a new API, header-based versioning is the default choice.

---

## Background Services

When using `IHostedService` or `BackgroundService`, register them with factory lambdas and pass configuration as constructor parameters.

```csharp
TimeSpan pollingInterval = TimeSpan.FromMinutes(
    builder.Configuration.GetValue("MyService:PollingIntervalMinutes", defaultValue: 5));

builder.Services.AddHostedService(sp =>
    new MyBackgroundService(
        sp.GetRequiredService<IMyDependency>(),
        pollingInterval,
        sp.GetRequiredService<ILogger<MyBackgroundService>>()));
```

---

## Response Compression

Enable response compression for JSON APIs. Explicitly scope to relevant MIME types.

```csharp
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;

    options.MimeTypes =
    [
        "application/json",
        "application/problem+json",
    ];
});
```

Call `app.UseResponseCompression()` early in the middleware pipeline, before any middleware that writes response bodies.

---

## Mapping

Use manual mapping between entities and DTOs. Do not use AutoMapper, Mapster, or similar runtime reflection-based mapping libraries.

```csharp
// Do: Manual mapping methods on the DTO or as extension methods
public static class FilmMappingExtensions
{
    public static FilmResponse ToResponse(this Film film) =>
        new()
        {
            Id = film.Id,
            Title = film.Title,
            StudioName = film.Studio.Name,
            ReleaseYear = film.ReleaseDate.Year,
        };

    public static IReadOnlyList<FilmResponse> ToResponse(this IEnumerable<Film> films) =>
        films.Select(film => film.ToResponse()).ToList().AsReadOnly();
}
```

```csharp
// Do not: AutoMapper or similar libraries
builder.Services.AddAutoMapper(typeof(Program));

// Do not: Inline mapping scattered across endpoints
app.MapGet("/films/{id}", async (int id, IFilmRepository repository) =>
{
    Film film = await repository.GetByIdAsync(id);
    return new FilmResponse
    {
        Id = film.Id,
        Title = film.Title,
        // Repeated everywhere a Film is returned
    };
});
```