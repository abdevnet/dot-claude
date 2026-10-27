---
description: >-
  Fetch when generating, reviewing, or modifying outbound HTTP client code,
  HttpClient registration, IHttpClientFactory usage, or resilience/retry
  policies in any .NET project. Contains Swank-specific conventions for the
  Swank.Web.Client NuGet package, SwankHttpStandardResilienceOptions
  (rate limiter, total request timeout, retry, circuit breaker, attempt
  timeout), typed and named client registration, appsettings.json
  configuration schema, DefaultHttpClientHandler, and migration guidance
  from the legacy PolicyConfiguration pattern. When appsettings files are
  added or modified, also apply the csproj nesting rule from
  csharp-instructions.md.
---

# HttpClient and Resilience Standards

## IHttpClientFactory

Use `IHttpClientFactory` for creating `HttpClient` instances. Do not create `HttpClient` directly with `new HttpClient()`.

Both typed clients and named clients are acceptable. Choose based on project needs.

```csharp
// Do: Typed client via IHttpClientFactory (registered in DI)
public class ProductService : IProductService
{
    private readonly HttpClient _httpClient;

    public ProductService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }
}
```

```csharp
// Do not: Manual HttpClient instantiation
public class ProductService : IProductService
{
    private readonly HttpClient _httpClient = new();

    public async Task<Product> GetProductAsync(string productNumber,
        CancellationToken cancellationToken)
    {
        // This causes socket exhaustion in long-lived services
    }
}
```

## Swank.Web.Client NuGet Package

Use the `Swank.Web.Client` package for typed HttpClient registration with built-in resilience.

```xml
<PackageReference Include="Swank.Web.Client" Version="[Latest Version]" />
```

## Registration

Register a typed HttpClient with the `AddHttpClient` extension method, specifying the resilience options type and client options type. The configuration section name points to a section in `appsettings.json` that contains both the resilience policy and client options.

```csharp
services.AddHttpClient<IProductService, ProductService, SwankHttpStandardResilienceOptions, HttpClientOptions>(
    configuration, "ProductServiceSettings");
```

The type parameters are:

- `TClient` - The service interface (e.g., `IProductService`)
- `TImplementation` - The service implementation (e.g., `ProductService`)
- `TPolicyConfiguration` - The resilience options type. Use `SwankHttpStandardResilienceOptions` for new projects.
- `THttpClientOptions` - The client options type. Use `HttpClientOptions` unless custom options are needed.

An overload accepts a fifth type parameter, `THttpClientHandler`, for providing a custom `HttpClientHandler`. When omitted, `DefaultHttpClientHandler` is used, which enables GZip and Deflate decompression. Only use a custom handler when the default behavior is not appropriate.

## Configuration

All resilience and client settings are driven by `appsettings.json`. The configuration section is split into two parts: `Policy` (resilience pipeline) and `ClientOptions` (base address, timeout, authorization).

```json
{
  "ProductServiceSettings": {
    "Policy": {
      "EnableRateLimiter": true,
      "EnableTotalRequestTimeout": true,
      "EnableRetry": true,
      "EnableCircuitBreaker": true,
      "EnableAttemptTimeout": true,

      "RateLimiter": {
        "DefaultRateLimiterOptions": {
          "PermitLimit": 1000,
          "QueueProcessingOrder": "OldestFirst",
          "QueueLimit": 0
        }
      },
      "TotalRequestTimeout": {
        "Timeout": "00:00:30"
      },
      "Retry": {
        "ShouldRetryAfterHeader": true,
        "MaxRetryAttempts": 3,
        "BackoffType": "Exponential",
        "UseJitter": true,
        "Delay": "00:00:02"
      },
      "CircuitBreaker": {
        "FailureRatio": 0.1,
        "MinimumThroughput": 100,
        "SamplingDuration": "00:00:30",
        "BreakDuration": "00:00:05"
      },
      "AttemptTimeout": {
        "Timeout": "00:00:06"
      }
    },
    "ClientOptions": {
      "Timeout": "00:05:00",
      "BaseAddress": "https://productservice.dev.ncus.apps.swankmp.net/",
      "AuthorizationHeader": "Bearer YourTokenHere"
    }
  }
}
```

### Resilience Pipeline

The `SwankHttpStandardResilienceOptions` pattern builds on Microsoft's standard resilience pipeline. Each step can be independently enabled or disabled via the `Enable*` boolean properties. The steps execute in this order:

1. Rate Limiter
2. Total Request Timeout
3. Retry
4. Circuit Breaker
5. Attempt Timeout

For detailed documentation on each step and its defaults, see Microsoft's [HTTP resilience documentation](https://learn.microsoft.com/en-us/dotnet/core/resilience/http-resilience) and the [standard resilience pipeline blog post](https://devblogs.microsoft.com/dotnet/building-resilient-cloud-services-with-dotnet-8/#standard-resilience-pipeline6).

### ClientOptions

The `ClientOptions` section configures the underlying `HttpClient`:

- `BaseAddress` - The base URL for the service.
- `Timeout` - The `HttpClient.Timeout` value.
- `AuthorizationHeader` - Optional. Sets the `Authorization` header on all requests from this client.

### Validation

The package validates configuration at startup. It will throw `InvalidOperationException` if:

- The `TotalRequestTimeout` exceeds the `HttpClient.Timeout`.
- The `AttemptTimeout` exceeds the `HttpClient.Timeout`.
- The `AttemptTimeout` exceeds the `TotalRequestTimeout`.
- The circuit breaker's `SamplingDuration` is less than double the `AttemptTimeout`.

Set `ClientOptions.Timeout` high enough to accommodate the full resilience pipeline, including all retries and backoff delays.

## Legacy PolicyConfiguration Pattern

Older projects may use the `PolicyConfiguration` pattern, which is the original Polly-based implementation predating Microsoft's `HttpStandardResilienceOptions`. It is registered the same way but with `PolicyConfiguration` as the resilience type:

```csharp
services.AddHttpClient<IService, Service, PolicyConfiguration, HttpClientOptions>(
    configuration, "ServiceSettings");
```

New projects should use `SwankHttpStandardResilienceOptions`. Existing projects using `PolicyConfiguration` should migrate when practical.
