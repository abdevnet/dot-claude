---
description: >-
  Fetch when generating, reviewing, or modifying API controllers or endpoints
  that use SwankResult or SwankResult<T> as the response type, or when working
  with code that consumes APIs returning SwankResult responses. Contains the
  SwankResult type structure, factory methods, properties, and usage patterns.
  Also fetch when you see SwankResult referenced in existing code and need to
  understand the convention.
---

# SwankResult Response Wrapper

## Overview

`SwankResult<T>` is a standardized response wrapper used by many (but not all) internal Swank APIs. The type lives in the `Swank.Web` namespace.

New APIs are not required to use `SwankResult`. The ASP.NET Core instructions document covers ProblemDetails as the recommended error response pattern for new applications. However, many existing APIs return `SwankResult` and any code that produces or consumes these APIs should follow the conventions below.

## Type Structure

### SwankResult&lt;T&gt;

```csharp
public class SwankResult<T>
{
    public bool IsSuccessResult { get; set; }
    public int ResultValue { get; set; }
    public string Message { get; set; }
    public string? ExceptionDetails { get; set; }
    public T? Payload { get; set; }
}
```

`ResultValue` is an application-specific result code. This is not the HTTP status code, though some APIs use the HTTP status code value here by convention.

### SwankResult

The non-generic version inherits from `SwankResult<object?>` and is used for endpoints that do not return data. The payload is always `null`.

## Factory Methods

Use the static factory methods to create instances. Do not call the constructor directly.

```csharp
// Success with payload
SwankResult<Product>.CreateSuccessResult(product)
SwankResult<Product>.CreateSuccessResult(product, message: "Found", resultValue: 200)

// Error with payload type
SwankResult<Product>.CreateErrorResult(resultValue: 404, message: "Product not found")
SwankResult<Product>.CreateErrorResult(resultValue: 500, message: "Error", exceptionDetails: ex.Message)

// Success without payload
SwankResult.CreateSuccessResult()
SwankResult.CreateSuccessResult(message: "Operation completed", resultValue: 0)

// Error without payload
SwankResult.CreateErrorResult(resultValue: 500, message: "Something went wrong")
```

## Usage in API Responses

Set the HTTP status code on the response separately. The `SwankResult` carries the application-level result.

```csharp
[HttpGet("{productNumber}")]
[ProducesResponseType(typeof(SwankResult<Product>), StatusCodes.Status200OK)]
[ProducesResponseType(typeof(SwankResult<Product>), StatusCodes.Status404NotFound)]
public async Task<SwankResult<Product>> GetProductAsync(
    [FromRoute] string productNumber, CancellationToken cancellationToken)
{
    Product? product = await _productService.GetProductAsync(productNumber, cancellationToken);

    if (product is null)
    {
        Response.StatusCode = StatusCodes.Status404NotFound;
        return SwankResult<Product>.CreateErrorResult(404, "Product not found");
    }

    return SwankResult<Product>.CreateSuccessResult(product);
}
```

## Consuming SwankResult APIs

Check `IsSuccessResult` before accessing `Payload`:

```csharp
SwankResult<Product>? result = await _productClient.GetProductAsync(productNumber);

if (result is null || !result.IsSuccessResult)
{
    // Handle error, log result.Message if available
}

Product product = result.Payload;
```
