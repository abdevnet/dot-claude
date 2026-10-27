---
description: >-
  Fetch when generating, reviewing, or modifying code that calls the Product
  Publicity API, registers IProductPublicityService or ProductPublicityService,
  configures the ProductPublicityApi appsettings section, or works with types
  in the ProductPublicityApi.Data.Models.V3 or
  ProductPublicityApi.Client.Interfaces namespaces. Covers the Product and
  ProductRank models, typed HttpClient registration, environment-specific
  base addresses, bearer token configuration, and all child model types
  returned by the API. When appsettings files are added or modified, also apply
  the csproj nesting rule from csharp-instructions.md.
---

# Product Publicity API Client

## Overview

The Product Publicity API provides product metadata for Swank titles, including synopses, cast and crew, ratings, genres, assets, rights lines, episodes, and release information. Consuming applications use the `IProductPublicityService` interface from the `ProductPublicityApi.Client` NuGet package.

## NuGet Package

```xml
<PackageReference Include="ProductPublicityApi.Client" Version="[Latest Version]" />
```

## Core Types and Namespaces

| Type | Namespace |
|---|---|
| `IProductPublicityService` | `ProductPublicityApi.Client.Interfaces` |
| `ProductPublicityService` | `ProductPublicityApi.Client.Services` |
| `Product` | `ProductPublicityApi.Data.Models.V3` |
| `ProductRank` | `ProductPublicityApi.Data.Models.V3` |

All child models (`Release`, `RightsLine`, `Synopsis`, `Asset`, `CastMember`, `CrewMember`, `Rating`, `Genre`, `Episode`, `Identifier`, `LocalizedTitle`, `LocalizedTag`, `Distributor`, `RightsStatus`, `RightsRestriction`, `RightsLineRestriction`, `ReleaseDetail`, `PublicityTag`, `Person`) also live in `ProductPublicityApi.Data.Models.V3`.

---

## Configuration

The API client reads its settings from the `ProductPublicityApi` configuration section. Each environment has its own base address. The bearer token is shared across all environments and only needs to be set once in the base `appsettings.json`.

### Hard Rule: Bearer Token Comment

When adding or creating `ProductPublicityApi` configuration in appsettings files, follow this process:

1. If all correct settings already exist, do nothing.
2. If the files exist but values are missing, add them.
3. If the files do not exist, create them with the correct values.

When settings are added or created, always include the bearer token link comment. Leave the `BearerToken` value as an empty string and add a `//` comment pointing to the source. Do not skip this step.

```json
// Always include when BearerToken is added
// Get or create a valid bearer token at:
// https://dev.azure.com/swankmp/Web%20Sites/_git/product-publicity-api?path=/ProductPublicityApi/appsettings.json&version=GBmain&line=5&lineEnd=5&lineStartColumn=21&lineEndColumn=53&lineStyle=plain&_a=contents
"BearerToken": ""
```

### appsettings.json

Used for local development and the deployed Dev environment.

```json
{
  "ProductPublicityApi": {
    "BaseAddress": "https://productpublicityapi.dev.ncus.apps.swankmp.net/",
    // Get or create a valid bearer token at:
    // https://dev.azure.com/swankmp/Web%20Sites/_git/product-publicity-api?path=/ProductPublicityApi/appsettings.json&version=GBmain&line=5&lineEnd=5&lineStartColumn=21&lineEndColumn=53&lineStyle=plain&_a=contents
    "BearerToken": ""
  }
}
```

### appsettings.QA.json

```json
{
  "ProductPublicityApi": {
    "BaseAddress": "https://productpublicityapi.qa.ncus.apps.swankmp.net/"
  }
}
```

### appsettings.Staging.json

```json
{
  "ProductPublicityApi": {
    "BaseAddress": "https://productpublicityapi.staging.ncus.apps.swankmp.net/"
  }
}
```

### appsettings.Production.json

```json
{
  "ProductPublicityApi": {
    "BaseAddress": "https://productpublicityapi.swankmp.net/"
  }
}
```

Only override `BaseAddress` per environment. The `BearerToken` value in `appsettings.json` applies to all environments.

---

## Registration

Register the typed `HttpClient` during service configuration. Read both values from configuration and pass them to the client factory delegate.

```csharp
using ProductPublicityApi.Client.Interfaces;
using ProductPublicityApi.Client.Services;

string productPublicityApiBaseAddress = configuration
    .GetSection("ProductPublicityApi:BaseAddress").Value
    ?? throw new InvalidOperationException("Missing configuration: ProductPublicityApi:BaseAddress");

string productPublicityApiBearerToken = configuration
    .GetSection("ProductPublicityApi:BearerToken").Value
    ?? throw new InvalidOperationException("Missing configuration: ProductPublicityApi:BearerToken");

services.AddHttpClient<IProductPublicityService, ProductPublicityService>(client =>
{
    client.BaseAddress = new Uri(productPublicityApiBaseAddress);
    client.DefaultRequestHeaders.Authorization =
        new AuthenticationHeaderValue("Bearer", productPublicityApiBearerToken);
});
```

---

## IProductPublicityService

The interface exposes four methods:

### GetProductAsync

Returns a single `Product` by its ARC product number. Returns `null` when the product is not found.

```csharp
Task<Product> GetProductAsync(
    string productNumber,
    CancellationToken cancellationToken = default,
    bool useCache = false);
```

### GetProductsAsync

Returns multiple products in a single call.

```csharp
Task<IList<Product>> GetProductsAsync(
    List<string> productNumbers,
    CancellationToken cancellationToken = default,
    bool useCache = false);
```

### GetProductRankingsAsync

Returns product rankings for a given sales division and organization type.

```csharp
Task<IList<ProductRank>> GetProductRankingsAsync(
    string salesDivision,
    string orgType,
    CancellationToken cancellationToken = default);
```

### GetChangedProductsByDateRangeAsync

Returns product numbers for products whose data changed within the given date range.

```csharp
Task<IList<string>> GetChangedProductsByDateRangeAsync(
    DateTime startDate,
    DateTime endDate,
    CancellationToken cancellationToken = default);
```

---

## Usage

Inject `IProductPublicityService` and call the desired method. Check for null results where applicable.

```csharp
using ProductPublicityApi.Client.Interfaces;
using ProductPublicityApi.Data.Models.V3;

public class CatalogService
{
    private readonly IProductPublicityService _productPublicityService;

    public CatalogService(IProductPublicityService productPublicityService)
    {
        ArgumentNullException.ThrowIfNull(productPublicityService);
        _productPublicityService = productPublicityService;
    }

    public async Task<Product?> GetProductAsync(
        string productNumber,
        CancellationToken cancellationToken = default)
    {
        Product product = await _productPublicityService
            .GetProductAsync(productNumber, cancellationToken);

        if (product is null)
        {
            return null;
        }

        return product;
    }
}
```

---

## Product Model

`Product` is the root response type returned by `GetProductAsync` and `GetProductsAsync`. It contains scalar properties and collection navigations for all product metadata.

### Scalar Properties

| Property | Type | Description |
|---|---|---|
| `Title` | `string` | Display title (coalesced: Swank Override > Rovi Master Title > ARC Title) |
| `SwankTitle` | `string` | ARC Product Name |
| `Type` | `string` | Product type (Movie, Series, Episode, OneTime) |
| `OriginalType` | `string` | Original product type, also known as ProgramType |
| `ReleaseYear` | `int?` | Release year |
| `Runtime` | `int?` | Published runtime in minutes |
| `Remove` | `bool` | Whether the product has been removed |
| `Color` | `string` | Color type (e.g. Color, Black and White) |
| `LastModified` | `DateTime?` | Last modification timestamp |
| `ParentProductNumber` | `string` | Parent product number (for episodes and seasons) |
| `Studio` | `string` | Studio name |
| `Category` | `string` | Category |
| `Subcategory` | `string` | Subcategory |
| `Rating` | `string` | Rating value |
| `SeasonNumber` | `int?` | Season number |
| `EpisodeNumber` | `int?` | Episode number |
| `SequenceNumber` | `int?` | Sequence number |

### Collection Properties

| Property | Type | Description |
|---|---|---|
| `Identifiers` | `IList<Identifier>` | Product identifiers (ProductNumber, CosmoID, SwankFilmID, etc.) |
| `Releases` | `IEnumerable<Release>` | Release information by locale |
| `Titles` | `IEnumerable<LocalizedTitle>` | Localized titles |
| `Synopses` | `IEnumerable<Synopsis>` | Synopses by locale and source type |
| `Genres` | `IEnumerable<Genre>` | Genres by locale |
| `Tags` | `IEnumerable<LocalizedTag>` | Localized tags |
| `Cast` | `IEnumerable<CastMember>` | Cast members with part names |
| `Crew` | `IEnumerable<CrewMember>` | Crew members (directors) |
| `Ratings` | `IEnumerable<Rating>` | Ratings by authority (MPAA, US TV) |
| `Assets` | `IEnumerable<Asset>` | Publicity assets (images, trailers) |
| `Rights` | `IEnumerable<RightsLine>` | Market-specific rights lines |
| `Episodes` | `IEnumerable<Episode>` | Child episodes (for series products) |

### Computed Properties

`ProductNumber` extracts the ARC product number from the `Identifiers` collection. It is not serialized in API responses.

`EarliestAvailabilityDateSortBy` returns the earliest availability date with priority: Colleges rights first, then OnBoard rights, then the minimum across all other rights. Returns `null` when no rights exist.

---

## Child Models

### Identifier

Identifies the product across systems. Common identifier names are defined as constants: `ProductNumber`, `CosmoID`, `SwankFilmID`, `EIDRIdentifier`, `MovieIdentifier`, `FilmMetadataID`, `ProductID`.

### Synopsis

Contains synopsis text for a locale. Source type constants: `PhoneSynopsis`, `TabletSynopsis`, `WebSynopsis`, `Default`, `Plot Synopsis`.

### Rating

A rating with an `Authority` (e.g. MPAA, US TV) and `Value`. Implements value equality on `Authority` and `Value`.

### Asset

A publicity asset with `Name`, `AssetType`, `FileType`, `Location` (URL), `Locale`, `SourceSystem`, and `AltText`.

### Person, CastMember, and CrewMember

`Person` is the base class with `Name`, `DisplayOrder`, `Role`, and `Headshot`. `CastMember` extends `Person` with `PartName`. `CrewMember` extends `Person` with no additional properties.

### RightsLine

Defines market-specific rights for a product. Key properties include `SalesDivision`, `OrganizationType`, `EarlyWindowDate`, `GeneralAvailabilityDate`, `MarketRightsStartDate`, `MarketRightsEndDate`, `DownloadRightsStartDate`, `DownloadRightsEndDate`, `ExcludeFromWebsiteCatalog`, `Status` (array of `RightsStatus`), and `Restrictions` (array of `RightsLineRestriction`).

`Distributors` is a computed property parsed from a pipe-delimited backing field.

`AvailablilityDateSortBy` is a computed property that coalesces `EarlyWindowDate`, `GeneralAvailabilityDate`, and `MarketRightsStartDate`, falling back to January 1 of the release year when the resolved date is more than one year beyond the release year.

### RightsStatus

Defines the current status of a rights line (e.g. EarlyWindow, NewRelease) with `Name`, `StartDate`, `EndDate`, and `DateConfirmed`.

### RightsLineRestriction

A restriction on a rights line with `Type`, `DisplayName`, `StartDate`, and `EndDate`. A null `EndDate` indicates the restriction lasts forever.

### RightsRestriction

An internal rights restriction record with `SalesDivision`, `OrganizationType`, `RestrictionType` (an `AvailableRightsStatus` enum value), `RestrictionName`, `StartDate`, `EndDate`, `ProductNumber`, `TitleId`, `AgreementName`, and `WebsiteProducerName`. This model is not serialized in API responses.

### Release and ReleaseDetail

`Release` contains region-specific release dates (`HomeVideo`, `Theatrical`) and a collection of `ReleaseDetail` entries. `ReleaseDetail` has `Name`, `Date`, and `UPCID`.

### LocalizedTitle

A localized title with `Locale`, `Text`, and `SourceType`. Source type constants: `EpisodeTitle`, `OriginalTitle`, `SecondaryTitle`, `MasterTitle`, `Default`.

### LocalizedTag

A localized tag with `Locale`, `Text`, and `SourceType`. Includes a static `TagComparer` for equality comparison.

### Genre

A genre with `Locale` and `Text`.

### Distributor

A distributor with a `Name` property.

### Episode

A child episode with `ProductNumber`, `Title`, `SwankTitle`, `SeasonNumber`, `EpisodeNumber`, `SequenceNumber`, and localized `Titles`.

### ProductRank

Returned by `GetProductRankingsAsync`. Contains `Rank`, `ProductNumber`, and `Title`.
