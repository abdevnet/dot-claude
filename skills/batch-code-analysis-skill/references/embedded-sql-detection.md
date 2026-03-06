# Embedded SQL Detection

When reviewing repository/data access layer code (e.g., files with "Repository", "DataAccess", "Dal" in the path or name), check for embedded SQL queries even if the primary language is C#/Java/etc.

## Indicators

- String literals containing SQL keywords: SELECT, INSERT, UPDATE, DELETE, FROM, WHERE
- ORM/data access patterns:
  - Dapper: `connection.QueryAsync<T>("SELECT ...")`, `connection.ExecuteAsync("INSERT ...")`
  - ADO.NET: `SqlCommand`, `cmd.CommandText = "SELECT ..."`
  - Entity Framework raw SQL: `FromSqlRaw()`, `ExecuteSqlRaw()`
  - JDBC: `executeQuery("SELECT ...")`, `executeUpdate("INSERT ...")`

## Action

If embedded SQL is detected, load both the primary language standards (C#, Java, etc.) AND SQL Server standards, then pass both to workers.

### Example

```csharp
// DeviceRegistrationRepository.cs contains:
private static string GetCustomerSql()
{
    return @"SELECT [Id], [Name] FROM [dbo].[Customer] WHERE [Id] = @CustomerId";
}
```

Workers should review:
- **C# aspects**: method naming, string formatting, parameterization usage
- **SQL aspects**: schema prefixes, parameterization, column naming, data types

Do not skip SQL standards even if SQL is "just strings" in the code — query quality, injection protection, and standards adherence are critical.
