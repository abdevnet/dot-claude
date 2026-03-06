# SQL Server Coding Standards

## Naming and Schemas

### Schema Usage
- Using schema names in code is desirable as it simplifies refactoring when moving objects to new schemas and can provide performance benefits by explicitly telling the optimizer where to look for objects.
- Guidelines for schema name usage:
  - **Single schema (dbo only)**: Desirable but not necessary
  - **Three or more schemas**: Desirable to include schema names
- Use schemas to separate duty and identify related objects. Schemas can also be used to secure objects.
  - Instead of: `dbo.PublicityObjectName` or `dbo.ARC_ObjectName`
  - Use: `publicity.AssetType` or `ARC.ObjectName`

### General Naming Conventions
- Avoid using underscores in naming databases, tables, and columns.
  - **Exception**: If working with a pre-existing database that already uses underscores, continue using them for consistency.
- Avoid using Hungarian prefix notation:
  - ❌ `spProcedureName`, `tblTableName`, `stColumnName`
- Tables should be defined in the singular form, columns in the singular (where it makes sense).
- Table identity columns should be named `Id` (not `TableNameId`).

### Object-Specific Naming Conventions

| Object Type | Convention | Example |
|------------|------------|---------|
| Clustered Index | `CIX_IndexName` | `CIX_AssetByDate` |
| Nonclustered Index | `NCIX_IndexName` | `NCIX_UserEmail` |
| Unique Constraint | `UQ_Name` | `UQ_Email` |
| Check Constraint | `CK_Name` | `CK_PositiveAmount` |
| Default Constraint | `DF_Name` | `DF_CreatedDate` |
| Primary Key | `SK_KeyName` or `NK_KeyName` | `SK_Asset` (surrogate), `NK_User` (natural) |
| Foreign Key | `FK_KeyName` | `FK_Asset_User` |
| View | `VW_Name` | `VW_ActiveUsers` |
| Scalar Function | `SF_Name` | `SF_CalculateDiscount` |
| Table Valued Function | `TVF_Name` or `MTVF_Name` | `TVF_SplitString`, `MTVF_GetHierarchy` |

#### Foreign Key Naming Convention
Enforce explicit foreign key naming with a `FK_` prefix:
**Pattern**: `[FK_TableName_ReferencedTableName_ReferencedColumnName]`
This pattern ensures:
- Uniqueness across the database (prevents constraint name conflicts)
- Self-documenting names that clearly show the source table, referenced table, and column
- Consistency across all repositories following this naming standard


## Variables and Parameters

### Variable Declarations
- Use one `DECLARE` statement for all variables.
- Variables should be set on the same line unless coming from a `SELECT`.

```sql
DECLARE @UserId INT = 1,
        @StartDate DATE = '2025-01-01',
        @EndDate DATE = '2025-12-31';
```

### Parameter Best Practices
- When a parameter has a wide range of potential values, consider using query hints to address parameter sniffing:
  - `OPTION (OPTIMIZE FOR UNKNOWN)`
  - `OPTION (OPTIMIZE FOR @Variable)`
  - `OPTION (RECOMPILE)`
- Avoid using `varchar(max)` in a variable or parameter unless necessary.
- When developing a stored procedure with parameters, include commented values for testing. Templates are a good supporting tool for this.

### Multi-Valued Parameters
- When working with a multi-valued parameter that requires a split function:
  - ✅ `INNER JOIN` to the split function
  - ❌ Do not add as a sub-select in the `WHERE` clause or `CROSS APPLY` to the function

## Data Types

### Date and Time Types
- **Use `datetime2` as the default** for all date/time columns
  - Provides better precision (100 nanoseconds vs 3.33 milliseconds)
  - More efficient storage (6-8 bytes vs 8 bytes)
  - Wider date range (0001-01-01 to 9999-12-31)
  - Modern standard recommended by Microsoft
- Use `datetime` only when integrating with legacy systems that don't support datetime2
- If a date field only needs short date and not time, use the `date` data type

### String Types
- Avoid using `(n)varchar(MAX)`. Data length shouldn't be greater than the maximum length of the data in the column.
- ❌ Never use `ntext`, `text`, or `image` data types as they are deprecated

### Numeric Types
- When using an `IDENTITY` column, choose an integer type that will support future growth (`int`, `bigint`)

## Table Definitions

### Column Nullability
- **Always specify NULL or NOT NULL explicitly** in column declarations
- Never omit the NULL/NOT NULL specification
- **Align NULL and NOT NULL keywords in column form** for easier viewing by humans
- Use extra spacing between the data type and NULL/NOT NULL to ensure vertical alignment

```sql
-- ✅ Good - Explicit nullability with aligned keywords
CREATE TABLE dbo.Customer
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    Name         NVARCHAR(100)         NOT NULL,
    Email        NVARCHAR(255)         NOT NULL,
    PhoneNumber  NVARCHAR(20)          NULL,
    Website      NVARCHAR(255)         NULL,
    CreatedDate  DATETIME2             NOT NULL
);

-- ✅ Good - Extra spacing used to maintain alignment with longer data types
CREATE TABLE dbo.Order
(
    Id                      INT IDENTITY(1,1)                     NOT NULL,
    OrderNumber             NVARCHAR(50)                          NOT NULL,
    CustomerConfigurationId INT                                   NOT NULL,
    TotalAmount             DECIMAL(18,2)                         NOT NULL,
    Notes                   NVARCHAR(MAX)                         NULL,
    IsActive                BIT               DEFAULT(1)          NOT NULL,
    DateInserted            DATETIME2         DEFAULT GETUTCDATE() NOT NULL
);

-- ❌ Bad - Omitted NULL specification
CREATE TABLE dbo.Customer
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    Name         NVARCHAR(100)         NOT NULL,
    Email        NVARCHAR(255)         NOT NULL,
    PhoneNumber  NVARCHAR(20),              -- Missing NULL
    Website      NVARCHAR(255)              -- Missing NULL
);

-- ❌ Bad - Not aligned in column form
CREATE TABLE dbo.Customer
(
    Id           INT IDENTITY(1,1) NOT NULL,
    Name         NVARCHAR(100) NOT NULL,
    Email        NVARCHAR(255) NOT NULL,
    PhoneNumber  NVARCHAR(20) NULL,
    Website      NVARCHAR(255) NULL
);
```

### Default Date Values
- Use `GETUTCDATE()` for default date/time columns (stores UTC time)
- ❌ Do not use `GETDATE()` (stores local server time)
- UTC dates ensure consistency across time zones and daylight saving changes

```sql
-- ✅ Good - Using GETUTCDATE()
CREATE TABLE dbo.Order
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    OrderNumber  NVARCHAR(50)          NOT NULL,
    CreatedDate  DATETIME2             NOT NULL DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2             NOT NULL DEFAULT GETUTCDATE()
);

-- ❌ Bad - Using GETDATE()
CREATE TABLE dbo.Order
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    OrderNumber  NVARCHAR(50)          NOT NULL,
    CreatedDate  DATETIME2             NOT NULL DEFAULT GETDATE(),
    ModifiedDate DATETIME2             NOT NULL DEFAULT GETDATE()
);
```

### BIT Column Defaults
- Use `DEFAULT(1)` or `DEFAULT(0)` for BIT column defaults
- ❌ Do not use `CONVERT([bit], 1)` or `CONVERT([bit], 0)`

```sql
-- ✅ Good - Using DEFAULT(1) and DEFAULT(0)
CREATE TABLE dbo.Product
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    ProductName  NVARCHAR(100)         NOT NULL,
    IsActive     BIT                   NOT NULL DEFAULT(1),
    IsDeleted    BIT                   NOT NULL DEFAULT(0),
    IsFeatured   BIT                   NULL     DEFAULT(0)
);

-- ❌ Bad - Using CONVERT
CREATE TABLE dbo.Product
(
    Id           INT IDENTITY(1,1)     NOT NULL,
    ProductName  NVARCHAR(100)         NOT NULL,
    IsActive     BIT                   NOT NULL DEFAULT CONVERT([bit], 1),
    IsDeleted    BIT                   NOT NULL DEFAULT CONVERT([bit], 0),
    IsFeatured   BIT                   NULL     DEFAULT CONVERT([bit], 0)
);
```

---

## Quick Reference

### ✅ Do
- Use schema names where desirable (especially with multiple schemas)
- Use singular form for tables and columns
- Use `datetime2` as the default for date/time columns (use `date` for date-only fields)
- Size varchar fields appropriately
- Consider parameter sniffing mitigation
- Use proper naming conventions for constraints and indexes
- Maintain consistency with pre-existing database conventions
- Always explicitly specify NULL or NOT NULL for all columns
- Align NULL/NOT NULL keywords in column form - use extra spacing to ensure vertical alignment
- Use `GETUTCDATE()` for default date/time values
- Use `DEFAULT(1)` or `DEFAULT(0)` for BIT column defaults

### ❌ Don't
- Use underscores in new databases (maintain consistency if already present)
- Use Hungarian notation (sp, tbl, st prefixes)
- Use deprecated data types (text, ntext, image)
- Use varchar(max) unnecessarily
- Include table name in Id columns
- Omit NULL or NOT NULL in column declarations
- Leave NULL/NOT NULL keywords misaligned - they should line up in column form
- Use `GETDATE()` for default dates (use `GETUTCDATE()` instead)
- Use `CONVERT([bit], 1)` or `CONVERT([bit], 0)` for BIT defaults
