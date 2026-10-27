---
description: >-
  Fetch when generating, reviewing, or modifying SQL Server schemas, queries,
  stored procedures, functions, or migrations. Contains Swank-specific
  conventions for uppercase keywords, leading comma SELECT lists, column
  alignment, explicit nullability, datetime2 defaults, GETUTCDATE(), naming
  conventions for constraints and indexes, table aliases and column
  qualification, explicit JOIN syntax, CTE preference, temp tables, MERGE
  upserts, NOLOCK policy, parameter sniffing mitigation, ORDER BY
  restrictions, table definition formatting, stored procedure conventions,
  reserved word bracketing, and transaction/error handling patterns.
---

# SQL Server Coding Standards

## Reserved and Problematic Identifier Bracketing

When a column or table name is a SQL Server reserved word or a commonly problematic word (e.g., `Name`, `Type`, `Status`, `Value`, `Order`, `Key`, `User`, `Role`, `Date`, `Index`), always wrap it in square brackets in every context. This applies to `SELECT` lists, `WHERE` clauses, `JOIN` conditions, `INSERT` column lists, `UPDATE SET` clauses, `ORDER BY`, `GROUP BY`, `MERGE` statements, and any other reference to the identifier. When in doubt, bracket it.

```sql
-- Do
SELECT
     c.Id
    ,c.[Name]
    ,c.[Status]
FROM dbo.Customer c

-- Do not
SELECT
     c.Id
    ,c.Name
    ,c.Status
FROM dbo.Customer c
```

## Keyword Casing and Formatting

- All SQL keywords must be UPPERCASE: `SELECT`, `FROM`, `WHERE`, `INNER JOIN`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, etc.
- Use leading commas in `SELECT` lists and column definitions. Each column on its own line.
- Only use semicolons where required (e.g., before a CTE's `WITH` clause). Do not terminate every statement with a semicolon.

```sql
-- Do
SELECT
     o.Id
    ,o.OrderNumber
    ,o.TotalAmount
    ,c.[Name]
FROM dbo.[Order] o
INNER JOIN dbo.Customer c
    ON o.CustomerId = c.Id
WHERE o.IsActive = 1

-- Do not
select
    o.Id,
    o.OrderNumber,
    o.TotalAmount,
    c.Name
from dbo.[Order] o
inner join dbo.Customer c
    on o.CustomerId = c.Id
where o.IsActive = 1;
```

## Naming and Schemas

### Schema Usage

- Use schema names where desirable, especially with multiple schemas. It simplifies refactoring and can provide optimizer hints.
  - **Single schema (dbo only)**: desirable but not necessary.
  - **Three or more schemas**: always include schema names.
- Use schemas to separate related objects instead of prefixing table names.

```sql
-- Do
publicity.AssetType
ARC.ObjectName

-- Do not
dbo.PublicityAssetType
dbo.ARC_ObjectName
```

### General Naming Conventions

- Avoid underscores in names for new databases. If working with a pre-existing database that uses underscores, continue using them for consistency.
- Do not use Hungarian prefix notation (`spProcedureName`, `tblTableName`, `stColumnName`).
- Tables should be singular. Columns should be singular where it makes sense.
- Table identity columns should be named `Id`, not `TableNameId`.

### Object-Specific Naming Conventions

| Object Type | Prefix | Example |
|---|---|---|
| Clustered Index | `CIX_` | `CIX_AssetByDate` |
| Nonclustered Index | `NCIX_` | `NCIX_UserEmail` |
| Unique Constraint | `UQ_` | `UQ_Email` |
| Check Constraint | `CK_` | `CK_PositiveAmount` |
| Default Constraint | `DF_` | `DF_CreatedDate` |
| Primary Key | `PK_` | `PK_Asset` |
| Foreign Key | `FK_` | `FK_Asset_User` |
| View | `VW_` | `VW_ActiveUsers` |
| Scalar Function | `SF_` | `SF_CalculateDiscount` |
| Table Valued Function | `TVF_` / `MTVF_` | `TVF_SplitString`, `MTVF_GetHierarchy` |

### Foreign Key Naming Convention

Pattern: `FK_TableName_ReferencedTableName`

## Table Definitions

### Identifier Formatting

Wrap all identifiers (schema names, table names, column names, constraint names) in square brackets in `CREATE TABLE` statements. Write data types in lowercase with a space before the size specifier.

```sql
-- Do
[Id]    int            IDENTITY (1, 1) NOT NULL
[Name]  varchar (100)  NOT NULL

-- Do not
Id    INT            IDENTITY(1,1) NOT NULL
Name  VARCHAR(100)   NOT NULL
```

### Column Layout

Use trailing commas in `CREATE TABLE` column definitions (unlike `SELECT` lists, which use leading commas). Vertically align column names, data types, and `NULL`/`NOT NULL` into distinct visual columns using spacing.

```sql
CREATE TABLE [mfg].[Job]
(
    [Id]         int            IDENTITY (1, 1) NOT NULL,
    [Type]       varchar (50)   NOT NULL,
    [Priority]   datetime2 (3)  NOT NULL,
    [Status]     varchar (50)   NOT NULL,
    [Reason]     varchar (512)  NULL,
    [CreatedOn]  datetime2 (3)  NOT NULL,
    [CreatedBy]  varchar (50)   NOT NULL,
    [UpdatedOn]  datetime2 (3)  NULL,
    [UpdatedBy]  varchar (50)   NULL,
    CONSTRAINT [PK_Job] PRIMARY KEY CLUSTERED ([Id] ASC),
)
GO
```

### Column Ordering

Order columns as follows:

1. Identity/primary key column(s) first.
2. Business columns next.
3. Audit columns last (`CreatedOn`, `CreatedBy`, `UpdatedOn`, `UpdatedBy`).

### Audit Columns

Include a standard set of four audit columns at the end of every table:

| Column | Type | Nullability |
|---|---|---|
| `CreatedOn` | `datetime2 (3)` | `NOT NULL` |
| `CreatedBy` | `varchar (50)` | `NOT NULL` |
| `UpdatedOn` | `datetime2 (3)` | `NULL` |
| `UpdatedBy` | `varchar (50)` | `NULL` |

The application is responsible for setting audit column values. Do not add `DEFAULT` constraints to audit columns.

### datetime2 Precision

Use `datetime2 (3)` explicitly. Do not use bare `datetime2` without a precision specifier.

```sql
-- Do
[CreatedOn]  datetime2 (3)  NOT NULL

-- Do not
[CreatedOn]  datetime2  NOT NULL
```

### Column Nullability

- Always specify `NULL` or `NOT NULL` explicitly on every column. Never omit it.
- Align `NULL` and `NOT NULL` keywords vertically using extra spacing.

### Default Date Values

- Use `GETUTCDATE()` for default date/time columns. Never use `GETDATE()`.

```sql
CREATE TABLE dbo.[Order]
(
    [Id]            int            IDENTITY (1, 1) NOT NULL,
    [OrderNumber]   nvarchar (50)  NOT NULL,
    [CreatedDate]   datetime2 (3)  NOT NULL DEFAULT GETUTCDATE(),
    [ModifiedDate]  datetime2 (3)  NOT NULL DEFAULT GETUTCDATE(),
)
```

### BIT Column Defaults

- Use `DEFAULT (1)` or `DEFAULT (0)`. Do not use `CONVERT([bit], 1)`.

```sql
CREATE TABLE dbo.[Product]
(
    [Id]           int             IDENTITY (1, 1) NOT NULL,
    [ProductName]  nvarchar (100)  NOT NULL,
    [IsActive]     bit             NOT NULL DEFAULT (1),
    [IsDeleted]    bit             NOT NULL DEFAULT (0),
)
```

### Constraints

Define named `PRIMARY KEY` and `FOREIGN KEY` constraints inline at the bottom of the `CREATE TABLE` body, after all columns. Primary keys must explicitly include `CLUSTERED` and `ASC`.

```sql
CREATE TABLE [mfg].[Task]
(
    [Id]         int            IDENTITY (1, 1) NOT NULL,
    [JobId]      int            NOT NULL,
    [Type]       varchar (50)   NOT NULL,
    [CreatedOn]  datetime2 (3)  NOT NULL,
    [CreatedBy]  varchar (50)   NOT NULL,
    [UpdatedOn]  datetime2 (3)  NULL,
    [UpdatedBy]  varchar (50)   NULL,
    CONSTRAINT [PK_Task] PRIMARY KEY CLUSTERED ([Id] ASC),
    CONSTRAINT [FK_Task_Job] FOREIGN KEY ([JobId]) REFERENCES [mfg].[Job] ([Id]),
)
GO
```

### Indexes

Create indexes as separate statements after the `CREATE TABLE`, each followed by `GO`. Use the `NCIX_` prefix for nonclustered indexes. Filtered indexes with `WHERE` clauses are acceptable where appropriate.

```sql
CREATE NONCLUSTERED INDEX NCIX_TypeStatusNextProcessingTime
    ON [mfg].[Task] ([Type], [Status], [NextProcessingTime])
    INCLUDE ([JobId], [Priority]);
GO
```

### GRANT Statements

Write one `GRANT` statement per role, using the `ON OBJECT::[schema].[table] TO [RoleName] AS [dbo]` syntax. Follow each with `GO`.

```sql
GRANT SELECT, INSERT, UPDATE ON OBJECT::[mfg].[Job] TO [SwankManufacturingJobsRole] AS [dbo];
GO

GRANT SELECT, UPDATE ON OBJECT::[mfg].[Job] TO [SwankManufacturingTasksRole] AS [dbo];
GO
```

### GO Separators

Terminate every logical block (`CREATE TABLE`, each `CREATE INDEX`, each `GRANT`) with `GO`.

### Complete Table Definition Example

```sql
CREATE TABLE [mfg].[Task]
(
    [Id]                  int            IDENTITY (1, 1) NOT NULL,
    [JobId]               int            NOT NULL,
    [Type]                varchar (50)   NOT NULL,
    [Priority]            datetime2 (3)  NOT NULL,
    [StartedOn]           datetime2 (3)  NULL,
    [FinishedOn]          datetime2 (3)  NULL,
    [Status]              varchar (50)   NOT NULL,
    [Reason]              varchar (512)  NULL,
    [AttemptCount]        int            NOT NULL DEFAULT ((0)),
    [NextProcessingTime]  datetime2 (3)  NULL,
    [CreatedOn]           datetime2 (3)  NOT NULL,
    [CreatedBy]           varchar (50)   NOT NULL,
    [UpdatedOn]           datetime2 (3)  NULL,
    [UpdatedBy]           varchar (50)   NULL,
    CONSTRAINT [PK_Task] PRIMARY KEY CLUSTERED ([Id] ASC),
    CONSTRAINT [FK_Task_Job] FOREIGN KEY ([JobId]) REFERENCES [mfg].[Job] ([Id]),
)
GO

CREATE NONCLUSTERED INDEX NCIX_TypeStatusNextProcessingTime
    ON [mfg].[Task] ([Type], [Status], [NextProcessingTime])
    INCLUDE ([JobId], [Priority]);
GO

GRANT SELECT, INSERT, UPDATE ON OBJECT::[mfg].[Task] TO [SwankManufacturingJobsRole] AS [dbo];
GO

GRANT SELECT, UPDATE ON OBJECT::[mfg].[Task] TO [SwankManufacturingTasksRole] AS [dbo];
GO
```

## Stored Procedures

### Header Comment Block

Include a comment block above the `CREATE PROCEDURE` statement with the author, creation date, description, and a usage example. There are no hard rules on the exact field names, labels, or date format. Use whatever is clear and consistent within the project.

```sql
/*

Author:         Brendan Ridenour
Create date:    October 26, 2023
Description:    Selects and reserves the next manufacturing
                task to process for the requested task type

Usage Example:
EXEC [mfg].[ReserveNextTask] 'Pro:Idiom Encrypting', 'ProIdiomEncryptor';

*/
CREATE PROCEDURE [mfg].[ReserveNextTask]
```

### CREATE PROCEDURE vs CREATE PROC

Both `CREATE PROCEDURE` and `CREATE PROC` are acceptable. There is no hard rule.

### Parameter Formatting

Use leading commas with no parentheses around the parameter list. Vertically align parameter names and data types.

```sql
-- Do
CREATE PROCEDURE [mfg].[ReserveNextTask]
     @taskType     varchar (50)
    ,@requestedBy  varchar (50)
AS

-- Do not
CREATE PROCEDURE [mfg].[ReserveNextTask]
(
    @taskType varchar(50),
    @requestedBy varchar(50)
)
AS
```

### Commented Template Variables

Include a commented-out `DECLARE` block below the `AS` keyword that mirrors the parameters with sample values. This allows quick F5 execution during development and testing.

```sql
CREATE PROCEDURE [mfg].[ReserveNextTask]
     @taskType    varchar (50)
    ,@requestedBy varchar (50)
AS

-- Template
--DECLARE @taskType varchar(50) = 'Pro:Idiom Encrypting'
--       ,@requestedBy varchar(50) = 'ProIdiomEncryptor';
```

### Transaction and Error Handling

When a stored procedure performs multiple write statements that need atomicity, use the following pattern:

1. `SET XACT_ABORT ON` before the transaction.
2. `BEGIN TRANSACTION` inside `BEGIN TRY`.
3. `COMMIT TRANSACTION` at the end of the `TRY` block.
4. `BEGIN CATCH` checks `@@TRANCOUNT > 0` before calling `ROLLBACK TRANSACTION`, then re-throws with `THROW`.

This pattern is not required for single-statement writes.

```sql
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Multiple write operations here

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH
```

### GRANT EXECUTE

Follow the same `GRANT` pattern used for tables. One statement per role, each followed by `GO`.

```sql
GRANT EXECUTE ON OBJECT::[mfg].[ReserveNextTask] TO [SwankManufacturingTasksRole] AS [dbo];
GO
```

### GO Separator

Terminate the `CREATE PROCEDURE` body and each `GRANT` with `GO`.

## Data Types

```sql
-- Do
CREATE TABLE dbo.[AuditLog]
(
    [Id]           int             IDENTITY (1, 1) NOT NULL,
    [EventDate]    datetime2 (3)   NOT NULL DEFAULT GETUTCDATE(),
    [DateOnly]     date            NOT NULL,
    [UserName]     nvarchar (100)  NOT NULL,
    [Description]  nvarchar (500)  NOT NULL,
)

-- Do not
CREATE TABLE dbo.[AuditLog]
(
    [Id]          int            IDENTITY (1, 1) NOT NULL,
    [EventDate]   datetime       NOT NULL DEFAULT GETDATE(),
    [UserName]    nvarchar (MAX) NOT NULL,
    [Description] ntext          NOT NULL,
)
```

- Use `DATETIME2` as the default for all date/time columns. Only use `DATETIME` for legacy system integration. Use `DATE` for date-only fields.
- Size `(N)VARCHAR` fields appropriately to the maximum expected data length. Do not use `(N)VARCHAR(MAX)` unless the data genuinely requires it.
- Never use deprecated types: `NTEXT`, `TEXT`, `IMAGE`.
- Choose an integer type that supports future growth for `IDENTITY` columns (`INT`, `BIGINT`).

## Variables and Parameters

- Use a single `DECLARE` statement for all variables.
- Set variable values on the same line unless the value comes from a `SELECT`.

```sql
DECLARE @UserId INT = 1
       ,@StartDate DATE = '2025-01-01'
       ,@EndDate DATE = '2025-12-31';
```

### Parameter Sniffing Mitigation

When a parameter has a wide range of potential values, add a query hint to prevent plan caching issues:

```sql
-- Use OPTIMIZE FOR UNKNOWN when the parameter value distribution is unpredictable
SELECT
     o.Id
    ,o.OrderNumber
    ,o.TotalAmount
FROM dbo.[Order] o
WHERE o.CustomerId = @CustomerId
OPTION (OPTIMIZE FOR UNKNOWN)

-- Use RECOMPILE for queries where optimal plans vary significantly per execution
SELECT
     o.Id
    ,o.OrderNumber
FROM dbo.[Order] o
WHERE (@Status IS NULL OR o.[Status] = @Status)
    AND (@StartDate IS NULL OR o.CreatedDate >= @StartDate)
OPTION (RECOMPILE)
```

Avoid `VARCHAR(MAX)` in parameters unless necessary. When developing stored procedures with parameters, include commented values for testing.

### Multi-Valued Parameters

When a multi-valued parameter requires a split function, use `INNER JOIN` to the split function. Do not use a sub-select in the `WHERE` clause or `CROSS APPLY` to the function.

```sql
-- Do: INNER JOIN to the split function
SELECT
     o.Id
    ,o.OrderNumber
FROM dbo.[Order] o
INNER JOIN dbo.TVF_SplitString(@OrderNumbers, ',') s ON o.OrderNumber = s.[Value]

-- Do not: Sub-select in WHERE
SELECT
     o.Id
    ,o.OrderNumber
FROM dbo.[Order] o
WHERE o.OrderNumber IN (SELECT [Value] FROM dbo.TVF_SplitString(@OrderNumbers, ','))

-- Do not: CROSS APPLY
SELECT
     o.Id
    ,o.OrderNumber
FROM dbo.[Order] o
CROSS APPLY dbo.TVF_SplitString(@OrderNumbers, ',') s
WHERE o.OrderNumber = s.[Value]
```

## Query Writing

### Table Aliases and Column Qualification

- Always alias tables. Use short abbreviations (`o`, `od`, `c`, `tsa`). This applies to both single-table and multi-table queries.
- Always qualify columns with the alias, even when unambiguous.

```sql
-- Do: Multi-table query with aliases and qualified columns
SELECT
     o.Id
    ,o.OrderNumber
    ,c.[Name]
    ,c.Email
FROM dbo.[Order] o
INNER JOIN dbo.Customer c
    ON o.CustomerId = c.Id
WHERE o.IsActive = 1

-- Do: Single-table query with alias and qualified columns
SELECT
     c.Id
    ,c.[Name]
    ,c.Email
FROM dbo.Customer c
WHERE c.IsActive = 1

-- Do not: Unaliased table with unqualified columns
SELECT
     Id
    ,Name
    ,Email
FROM dbo.Customer
WHERE IsActive = 1

-- Do not: Full table name used in place of an alias
SELECT
     Customer.Id
    ,Customer.Name
    ,Customer.Email
FROM dbo.Customer
WHERE Customer.IsActive = 1
```

### JOIN Syntax

- Always use explicit `INNER JOIN` / `LEFT JOIN` / `RIGHT JOIN` syntax. Never use implicit joins in the `FROM`/`WHERE` clause.

```sql
-- Do
SELECT
     o.Id
    ,c.[Name]
FROM dbo.[Order] o
INNER JOIN dbo.Customer c
    ON o.CustomerId = c.Id

-- Do not
SELECT
     o.Id
    ,c.Name
FROM dbo.[Order] o, dbo.Customer c
WHERE o.CustomerId = c.Id
```

### CTEs and Subqueries

- Prefer CTEs over subqueries for readability and reuse within a query.

```sql
-- Do
;WITH ActiveOrders AS
(
    SELECT
         o.Id
        ,o.CustomerId
        ,o.TotalAmount
    FROM dbo.[Order] o
    WHERE o.IsActive = 1
)
SELECT
     ao.Id
    ,c.[Name]
    ,ao.TotalAmount
FROM ActiveOrders ao
INNER JOIN dbo.Customer c
    ON ao.CustomerId = c.Id

-- Do not: deeply nested subquery
SELECT
     sub.Id
    ,c.[Name]
    ,sub.TotalAmount
FROM (
    SELECT
         o.Id
        ,o.CustomerId
        ,o.TotalAmount
    FROM dbo.[Order] o
    WHERE o.IsActive = 1
) sub
INNER JOIN dbo.Customer c
    ON sub.CustomerId = c.Id
```

### SELECT * Usage

- Never use `SELECT *` except inside `EXISTS` checks.

```sql
-- Acceptable
WHERE EXISTS (SELECT * FROM dbo.[Order] o WHERE o.CustomerId = c.Id)

-- Do not
SELECT * FROM dbo.Customer c
```

### ORDER BY

- Avoid `ORDER BY` in SQL when it is not necessary to the integrity of the query. Sorting should be handled at the application layer instead.
- `ORDER BY` is required when used with `TOP`, `OFFSET-FETCH`, or window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, `LEAD`, etc.). In these cases, always include it.
- Do not add `ORDER BY` to queries solely for display or presentation purposes. The consuming application code (LINQ, UI grid, etc.) is responsible for sort order.

```sql
-- Do: No ORDER BY when returning a full result set for the application to sort
SELECT
     o.Id
    ,o.OrderNumber
    ,o.CreatedDate
FROM dbo.[Order] o
WHERE o.IsActive = 1

-- Do: ORDER BY is required because TOP depends on it for correctness
SELECT TOP 10
     o.Id
    ,o.OrderNumber
FROM dbo.[Order] o
ORDER BY o.CreatedDate DESC

-- Do: ORDER BY is required because ROW_NUMBER depends on it
SELECT
     o.Id
    ,o.OrderNumber
    ,ROW_NUMBER() OVER (PARTITION BY o.CustomerId ORDER BY o.CreatedDate DESC) AS RowNum
FROM dbo.[Order] o

-- Do not: ORDER BY added purely for display sorting
SELECT
     o.Id
    ,o.OrderNumber
    ,o.CreatedDate
FROM dbo.[Order] o
WHERE o.IsActive = 1
ORDER BY o.CreatedDate DESC
```

### Temp Tables vs Table Variables

Prefer temp tables (`#table`) over table variables (`@table`).

```sql
-- Do: Temp table
CREATE TABLE #ActiveOrders
(
     OrderNumber  NVARCHAR(50)   NOT NULL
    ,TotalAmount  DECIMAL(18,2)  NOT NULL
)

INSERT INTO #ActiveOrders (OrderNumber, TotalAmount)
SELECT
     o.OrderNumber
    ,o.TotalAmount
FROM dbo.[Order] o
WHERE o.IsActive = 1

-- Do not: Table variable
DECLARE @ActiveOrders TABLE
(
    OrderNumber NVARCHAR(50) NOT NULL,
    TotalAmount DECIMAL(18,2) NOT NULL
)
```

### Upsert Pattern

Prefer `MERGE` for upsert operations.

```sql
-- Do: MERGE
MERGE dbo.Customer AS target
USING (SELECT @Id AS Id, @Name AS [Name], @Email AS Email) AS source
    ON target.Id = source.Id
WHEN MATCHED THEN
    UPDATE SET
         target.[Name] = source.[Name]
        ,target.Email = source.Email
        ,target.ModifiedDate = GETUTCDATE()
WHEN NOT MATCHED THEN
    INSERT ([Name], Email, CreatedDate)
    VALUES (source.[Name], source.Email, GETUTCDATE());

-- Do not: Separate existence check with INSERT/UPDATE
IF EXISTS (SELECT * FROM dbo.Customer WHERE Id = @Id)
BEGIN
    UPDATE dbo.Customer
    SET [Name] = @Name, Email = @Email, ModifiedDate = GETUTCDATE()
    WHERE Id = @Id
END
ELSE
BEGIN
    INSERT INTO dbo.Customer ([Name], Email, CreatedDate)
    VALUES (@Name, @Email, GETUTCDATE())
END
```

### NOLOCK Hints

- Do not use `NOLOCK` by default. Only use it in specific read-heavy reporting scenarios where dirty reads are acceptable.

### Error Raising

- Use `THROW` for raising errors. Do not use `RAISERROR`.

```sql
-- Do
THROW 50001, 'Order not found.', 1

-- Do not
RAISERROR('Order not found.', 16, 1)
```