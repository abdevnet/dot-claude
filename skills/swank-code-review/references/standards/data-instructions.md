---
description: >-
  Fetch when generating, reviewing, or modifying data access code, repository
  classes, database connection setup, or SQL queries in any .NET project.
  Contains Swank-specific conventions for the Swank.Data connection wrapper
  types (IDbConnectionWrapperFactory, IDbConnectionWrapper), database-specific
  marker interfaces, the repository pattern with Dapper, inline SQL and stored
  procedure conventions, EF Core usage in legacy applications,
  Swank.Data.RetryPolicies for transient SQL error handling, and the complete
  database reference with connection factory mappings and environment-specific
  connection strings. When appsettings files are added or modified, also apply
  the csproj nesting rule from csharp-instructions.md.
---

# Data Access Patterns

## Connection Factory Types

Swank uses a custom abstraction layer for database connections, provided by the `Swank.Data` package. This layer makes data access unit-testable by wrapping Dapper calls behind mockable interfaces.

### Core Types

Interfaces live in the `Swank.Data.Interfaces` namespace. Implementations live in the `Swank.Data` namespace.

- `IDbConnectionWrapperFactory` - Base interface for creating connections. Use `Create()` or `CreateAsync()`.
- `IDbConnectionWrapper` - Extends `IDbConnection` with Dapper query/execute methods. This is the mockable seam for unit testing.
- `SqlConnectionWrapperFactory` - Base implementation of `IDbConnectionWrapperFactory`.
- `DbConnectionWrapper` - Base implementation of `IDbConnectionWrapper`.

### Database-Specific Marker Interfaces

Each database has its own marker interface and implementation so that DI can distinguish between multiple connection strings:

```csharp
// Interface - empty, exists only for DI resolution
using Swank.Data.Interfaces;

public interface ISgcConnectionWrapperFactory : IDbConnectionWrapperFactory
{ }
```

```csharp
// Implementation - trivial pass-through
using Swank.Data.Interfaces;

namespace Swank.Data;

public class SgcConnectionWrapperFactory : SqlConnectionWrapperFactory, ISgcConnectionWrapperFactory
{
    public SgcConnectionWrapperFactory(string connectionString)
        : base(connectionString)
    { }
}
```

Follow this same pattern when adding a new database.

### Registration

Register each factory as a singleton with the connection string passed at registration time:

```csharp
string sgcConnectionString = builder.Configuration.GetConnectionString("SGC")
    ?? throw new InvalidOperationException("Missing connection string: SGC");

builder.Services.AddSingleton<ISgcConnectionWrapperFactory>(
    new SgcConnectionWrapperFactory(sgcConnectionString));
```

---

## Database Reference

This section maps every common Swank database to its connection factory types and connection string configuration. Use this reference when registering database dependencies or adding connection strings to appsettings files.

### Connection Factory Mapping

| Database | Connection String Key | Interface | Implementation |
|---|---|---|---|
| ADEBSDB | `ADEBSDB` | `IAdebsDbConnectionWrapperFactory` | `AdebsDbConnectionWrapperFactory` |
| Arc2 | `Arc2` | `IArc2ConnectionWrapperFactory` | `Arc2ConnectionWrapperFactory` |
| ArcBridge | `ArcBridge` | `IArcBridgeConnectionWrapperFactory` | `ArcBridgeConnectionWrapperFactory` |
| CENC | `CENC` | `ICencConnectionWrapperFactory` | `CencConnectionWrapperFactory` |
| CineLink | `CineLink` | `ICinelinkConnectionWrapperFactory` | `CinelinkConnectionWrapperFactory` |
| Contracts | `Contracts` | `IContractsConnectionWrapperFactory` | `ContractsConnectionWrapperFactory` |
| DMPDeployment | `DMPDeployment` | `IDmpConnectionWrapperFactory` | `DmpConnectionWrapperFactory` |
| Edelivery | `Edelivery` | `IEDeliveryDbConnectionWrapperFactory` | `EDeliveryDbConnectionWrapperFactory` |
| LabOrders | `LabOrders` | `ILabOrdersConnectionWrapperFactory` | `LabOrdersConnectionWrapperFactory` |
| MasterLibrary | `MasterLibrary` | `IMasterLibraryConnectionWrapperFactory` | `MasterLibraryConnectionWrapperFactory` |
| OneDRM | `OneDRM` | `IOneDrmConnectionWrapperFactory` | `OneDrmConnectionWrapperFactory` |
| RightsVault | `RightsVault` | `IRightsVaultConnectionWrapperFactory` | `RightsVaultConnectionWrapperFactory` |
| SGC | `SGC` | `ISgcConnectionWrapperFactory` | `SgcConnectionWrapperFactory` |
| SwankDRM | `SwankDRM` | `ISwankDrmConnectionWrapperFactory` | `SwankDrmConnectionWrapperFactory` |

### Environment-Specific Connection Strings

All databases exist in three environments. Each environment has its own SQL Server instance. Replace `{DatabaseName}` with the actual database name from the table above and `{Application Name}` with the name of the consuming application.

**Dev (local development and the deployed Dev environment):**

```
Server=dsql-primary.swankmp.local;Database={DatabaseName};Integrated Security=True;TrustServerCertificate=true;Application Name={Application Name}
```

**QA:**

```
Server=qsql-primary.swankmp.local;failover partner=qsql-backup.swankmp.local;Database={DatabaseName};Integrated Security=True;TrustServerCertificate=true;Application Name={Application Name}
```

**Production (used by apps deployed to Staging or Production):**

```
Server=psql-primary.swankmp.local;failover partner=psql-backup.swankmp.local;Database={DatabaseName};Integrated Security=True;TrustServerCertificate=true;Application Name={Application Name}
```

Key differences between environments:

- Dev uses `dsql-primary` with no failover partner.
- QA uses `qsql-primary` with `qsql-backup` as the failover partner.
- Production uses `psql-primary` with `psql-backup` as the failover partner.

### Configuring Connection Strings in appsettings Files

When adding or creating database configuration in appsettings files, follow this process:

1. If all correct settings already exist, do nothing.
2. If the files exist but values are missing, add them.
3. If the files do not exist, create them with the correct values.

Connection strings go in `appsettings.json` (Dev), `appsettings.QA.json` (QA), and `appsettings.Production.json` (Production). Only include the databases the application actually uses.

#### Example: An application named "Samsung Lynk Job Creator" using SGC and MasterLibrary

**appsettings.json:**

```json
{
  "ConnectionStrings": {
    "SGC": "Server=dsql-primary.swankmp.local;Database=SGC;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator",
    "MasterLibrary": "Server=dsql-primary.swankmp.local;Database=MasterLibrary;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator"
  }
}
```

**appsettings.QA.json:**

```json
{
  "ConnectionStrings": {
    "SGC": "Server=qsql-primary.swankmp.local;failover partner=qsql-backup.swankmp.local;Database=SGC;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator",
    "MasterLibrary": "Server=qsql-primary.swankmp.local;failover partner=qsql-backup.swankmp.local;Database=MasterLibrary;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator"
  }
}
```

**appsettings.Production.json:**

```json
{
  "ConnectionStrings": {
    "SGC": "Server=psql-primary.swankmp.local;failover partner=psql-backup.swankmp.local;Database=SGC;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator",
    "MasterLibrary": "Server=psql-primary.swankmp.local;failover partner=psql-backup.swankmp.local;Database=MasterLibrary;Integrated Security=True;TrustServerCertificate=true;Application Name=Samsung Lynk Job Creator"
  }
}
```

### Registration Example with Multiple Databases

```csharp
string sgcConnectionString = builder.Configuration.GetConnectionString("SGC")
    ?? throw new InvalidOperationException("Missing connection string: SGC");

string masterLibraryConnectionString = builder.Configuration.GetConnectionString("MasterLibrary")
    ?? throw new InvalidOperationException("Missing connection string: MasterLibrary");

builder.Services.AddSingleton<ISgcConnectionWrapperFactory>(
    new SgcConnectionWrapperFactory(sgcConnectionString));

builder.Services.AddSingleton<IMasterLibraryConnectionWrapperFactory>(
    new MasterLibraryConnectionWrapperFactory(masterLibraryConnectionString));
```

---

## Repository Pattern

All data access goes through repository interfaces. Do not call Dapper or EF Core directly from services, controllers, or endpoints.

```csharp
// Do: Data access through a repository
public class OrderService : IOrderService
{
    private readonly IOrderRepository _orderRepository;

    public OrderService(IOrderRepository orderRepository)
    {
        _orderRepository = orderRepository;
    }

    public async Task<Order?> GetOrderAsync(int orderNumber, CancellationToken cancellationToken)
    {
        return await _orderRepository.GetOrderAsync(orderNumber, cancellationToken);
    }
}
```

```csharp
// Do not: Dapper called directly from a service
using Swank.Data.Interfaces;

public class OrderService : IOrderService
{
    private readonly ISgcConnectionWrapperFactory _sgcConnectionWrapperFactory;

    public OrderService(ISgcConnectionWrapperFactory sgcConnectionWrapperFactory)
    {
        _sgcConnectionWrapperFactory = sgcConnectionWrapperFactory;
    }

    public async Task<Order?> GetOrderAsync(int orderNumber, CancellationToken cancellationToken)
    {
        const string query = "SELECT OrderNumber, Status FROM ARC_OrderDetail WHERE OrderNumber = @OrderNumber";
        using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
        return await sgc.QueryFirstOrDefaultAsync<Order>(query, new { OrderNumber = orderNumber });
    }
}
```

### Interface and Implementation

One repository interface per database or domain area. The implementation takes the database-specific connection factory as a constructor dependency.

```csharp
public interface IOrderRepository
{
    Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(int customerNumber, CancellationToken cancellationToken);
    Task<Order?> GetOrderAsync(int orderNumber, CancellationToken cancellationToken);
    Task UpdateStatusAsync(int orderNumber, string status, CancellationToken cancellationToken);
}
```

```csharp
using Swank.Data.Interfaces;

public class OrderRepository : IOrderRepository
{
    private readonly ISgcConnectionWrapperFactory _sgcConnectionWrapperFactory;

    public OrderRepository(ISgcConnectionWrapperFactory sgcConnectionWrapperFactory)
    {
        _sgcConnectionWrapperFactory = sgcConnectionWrapperFactory
            ?? throw new ArgumentNullException(nameof(sgcConnectionWrapperFactory));
    }

    public async Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(
        int customerNumber,
        CancellationToken cancellationToken)
    {
        const string query = @"
            SELECT OrderNumber, CustomerNumber, Status, OrderEntryDate
            FROM ARC_OrderDetail
            WHERE CustomerNumber = @CustomerNumber";

        using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
        IEnumerable<Order> results = await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });
        return results.ToList().AsReadOnly();
    }

    public async Task<Order?> GetOrderAsync(int orderNumber, CancellationToken cancellationToken)
    {
        const string query = @"
            SELECT OrderNumber, CustomerNumber, Status, OrderEntryDate
            FROM ARC_OrderDetail
            WHERE OrderNumber = @OrderNumber";

        using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
        return await sgc.QueryFirstOrDefaultAsync<Order>(query, new { OrderNumber = orderNumber });
    }

    public async Task UpdateStatusAsync(int orderNumber, string status, CancellationToken cancellationToken)
    {
        const string storedProcedure = "EXEC UpdateOrderStatus @OrderNumber, @Status";

        using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
        await sgc.ExecuteAsync(storedProcedure, new { OrderNumber = orderNumber, Status = status });
    }
}
```

### Key Conventions

**Connection lifecycle:** Create a new connection per method call with `using`. Do not reuse connections across methods.

```csharp
// Do: New connection per method, disposed at method end
using IDbConnectionWrapper connection = await _factory.CreateAsync(cancellationToken);
```

**CancellationToken:** Include `CancellationToken` on all async repository methods. Pass it to `CreateAsync()`. Passing it through to Dapper calls via `CommandDefinition` is also acceptable.

**Return types:** Prefer `IReadOnlyList<T>` or `IReadOnlyCollection<T>` over `IEnumerable<T>` for collection return types.

```csharp
// Preferred
public async Task<IReadOnlyList<Order>> GetOrdersAsync(CancellationToken cancellationToken)

// Acceptable
public async Task<IEnumerable<Order>> GetOrdersAsync(CancellationToken cancellationToken)
```

**Return models:** Return domain models or DTOs, not `dynamic`.

**Repository inheritance:** Repositories may inherit from a base repository when related repositories share common behavior.

**Testing:** When writing tests for repository query methods, see the Repository Testing section in the C# Unit Testing Standards document for SQL verification and parameter validation conventions.

---

## Dapper Usage

Dapper is the preferred ORM for new applications. Use it through the `IDbConnectionWrapper` methods, not as extension methods on a raw `IDbConnection`.

### Inline SQL

Define SQL as `const string` inside the method body. Use explicit column lists, never `SELECT *`.

```csharp
const string query = @"
    SELECT OrderNumber, CustomerNumber, Status
    FROM ARC_OrderDetail
    WHERE CustomerNumber = @CustomerNumber";

using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
return await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });
```

### Stored Procedures

Stored procedures can be called two ways. Both are acceptable:

```csharp
// Option 1: EXEC syntax as raw SQL
const string storedProcedure = "EXEC GetOrderDetails @OrderNumber, @ShipmentNumber";
return await sgc.QueryAsync<OrderDetail>(storedProcedure, new { orderNumber, shipmentNumber });
```

```csharp
// Option 2: CommandType.StoredProcedure
return await sgc.QueryAsync<OrderDetail>(
    new CommandDefinition(
        commandText: "[mfg].[GetOrderDetails]",
        parameters: new { orderNumber, shipmentNumber },
        commandType: CommandType.StoredProcedure,
        cancellationToken: cancellationToken));
```

### Parameters

Use anonymous objects for parameters. Property names must match SQL parameter names.

```csharp
// Do: Anonymous objects with matching property names
var parameters = new { orderNumber, shipmentNumber };
await sgc.QueryAsync<OrderDetail>(query, parameters);

// Do: Explicit property names when the variable name doesn't match
await sgc.QueryAsync<OrderDetail>(query, new { OrderNumber = orderNum });
```

### Query Methods

Choose the appropriate Dapper method for the expected result:

- `QueryAsync<T>` - Multiple rows
- `QueryFirstOrDefaultAsync<T>` - Single row that may not exist (returns `null`/`default`)
- `QueryFirstAsync<T>` - Single row that must exist (throws if empty)
- `QuerySingleOrDefaultAsync<T>` - Exactly zero or one row (throws if more than one)
- `QueryMultipleAsync` - Multiple result sets
- `ExecuteAsync` - Non-query commands (INSERT, UPDATE, DELETE)

### Multi-Mapping

Use Dapper's multi-mapping overloads to map joined queries to nested objects:

```csharp
return await sgc.Query<Order, Customer, Order>(
    query,
    map: (order, customer) =>
    {
        order.Customer = customer;
        return order;
    },
    queryParameters: parameters,
    splitOn: "CustomerId");
```

### Post-Query Processing

Light transformations are acceptable within the repository. Push business logic to the service layer.

```csharp
// Do: Simple transformations in the repository
public async Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(
    int customerNumber, CancellationToken cancellationToken)
{
    using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
    IEnumerable<Order> results = await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });

    return results
        .Select(order => order with { CustomerName = order.CustomerName.Trim() })
        .ToList()
        .AsReadOnly();
}
```

```csharp
// Do not: Business logic in the repository
public async Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(
    int customerNumber, CancellationToken cancellationToken)
{
    using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
    IEnumerable<Order> results = await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });

    return results
        .Where(order => order.IsEligibleForDiscount())
        .Select(order => order with { DiscountedTotal = order.Total * 0.9m })
        .ToList()
        .AsReadOnly();
}
```

### Sorting

Handle sorting at the application layer, not in SQL. Do not add `ORDER BY` to repository queries unless it is required for query correctness (e.g., `TOP`, `OFFSET-FETCH`, or window functions). When the caller needs sorted results, apply LINQ ordering after the query returns.

```csharp
// Do: Sort at the application layer (service or caller)
public async Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(
    int customerNumber, CancellationToken cancellationToken)
{
    const string query = @"
        SELECT o.OrderNumber, o.CustomerNumber, o.Status, o.OrderEntryDate
        FROM ARC_OrderDetail o
        WHERE o.CustomerNumber = @CustomerNumber";

    using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
    IEnumerable<Order> results = await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });
    return results.ToList().AsReadOnly();
}

// Caller applies sort order
IReadOnlyList<Order> orders = await _orderRepository.GetOrdersByCustomerAsync(customerNumber, cancellationToken);
List<Order> sorted = orders.OrderByDescending(order => order.OrderEntryDate).ToList();
```

```csharp
// Do not: ORDER BY in SQL for display sorting
public async Task<IReadOnlyList<Order>> GetOrdersByCustomerAsync(
    int customerNumber, CancellationToken cancellationToken)
{
    const string query = @"
        SELECT o.OrderNumber, o.CustomerNumber, o.Status, o.OrderEntryDate
        FROM ARC_OrderDetail o
        WHERE o.CustomerNumber = @CustomerNumber
        ORDER BY o.OrderEntryDate DESC";

    using IDbConnectionWrapper sgc = await _sgcConnectionWrapperFactory.CreateAsync(cancellationToken);
    IEnumerable<Order> results = await sgc.QueryAsync<Order>(query, new { CustomerNumber = customerNumber });
    return results.ToList().AsReadOnly();
}
```

---

## Retry Policies

The `Swank.Data.RetryPolicies` package provides Polly-based retry policies for transient SQL errors.

### Registration

Add retry policy configuration to `appsettings.json`:

```json
{
  "SqlRetryPolicy": {
    "RetryCount": 5,
    "RetryDuration": "00:00:05"
  }
}
```

Register with DI:

```csharp
RetryPolicyOptions options = new();
configuration.GetSection("SqlRetryPolicy").Bind(options);

services.AddDefaultSqlAsyncRetryPolicy(options);
```

### Custom Retry Policies

Override the `WaitAndRetryPolicy` to customize retry behavior:

```csharp
public class CustomRetryPolicy : SqlAsyncRetryPolicy
{
    public CustomRetryPolicy(RetryPolicyOptions options) : base(options)
    {
    }

    protected override AsyncRetryPolicy WaitAndRetryPolicy =>
        Policy.Handle<SqlException>(IsTransient)
            .Or<TimeoutException>()
            .WaitAndRetryAsync(
                _options.RetryCount,
                retryAttempt => _options.RetryDuration,
                (exception, delay, attempt, context) =>
                {
                    // Custom logging or handling
                });
}
```

Register a custom policy:

```csharp
services.AddSingleton<ISqlAsyncRetryPolicy, CustomRetryPolicy>();
```

---

## EF Core

EF Core is acceptable in legacy applications. Do not introduce EF Core in new projects where Dapper is a better fit.

When EF Core is used, follow the same repository interface pattern. The repository accepts a `DbContext` as a constructor dependency and uses it internally. Services depend on the repository interface, not on `DbContext` directly.

```csharp
public interface IWidgetRepository
{
    Task<IReadOnlyList<Widget>> GetAllAsync(CancellationToken cancellationToken);
    Task<Widget?> GetByIdAsync(int id, CancellationToken cancellationToken);
}
```

```csharp
public class WidgetRepository : IWidgetRepository
{
    private readonly WidgetDbContext _dbContext;

    public WidgetRepository(WidgetDbContext dbContext)
    {
        _dbContext = dbContext ?? throw new ArgumentNullException(nameof(dbContext));
    }

    public async Task<IReadOnlyList<Widget>> GetAllAsync(CancellationToken cancellationToken)
    {
        return await _dbContext.Widgets.ToListAsync(cancellationToken);
    }

    public async Task<Widget?> GetByIdAsync(int id, CancellationToken cancellationToken)
    {
        return await _dbContext.Widgets.FindAsync([id], cancellationToken);
    }
}
```

Do not expose `IQueryable<T>` from repository interfaces. Materialize queries inside the repository.