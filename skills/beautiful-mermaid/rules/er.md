# ER Diagrams

## Basics

```mermaid
erDiagram
  CUSTOMER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
  PRODUCT ||--o{ LINE_ITEM : "is in"
```

## Entity Attributes

```mermaid
erDiagram
  CUSTOMER {
    int id PK
    string name
    string email UK
    datetime created_at
  }
  ORDER {
    int id PK
    int customer_id FK
    decimal total
    string status
  }
  CUSTOMER ||--o{ ORDER : places
```

## Key Constraint Badges

| Badge | Meaning |
|-------|---------|
| `PK` | Primary Key |
| `FK` | Foreign Key |
| `UK` | Unique Key |

## Attribute Comments

```mermaid
erDiagram
  USER {
    int id PK "auto-increment"
    string email UK "must be valid"
    string password "bcrypt hashed"
  }
```

## Cardinality (Crow's Foot Notation)

| Left | Right | Meaning |
|------|-------|---------|
| `\|\|` | `\|\|` | Exactly one to exactly one |
| `\|\|` | `o\|` | Exactly one to zero or one |
| `\|\|` | `\|{` | Exactly one to one or more |
| `\|\|` | `o{` | Exactly one to zero or more |
| `o\|` | `o{` | Zero or one to zero or more |
| `}o` | `o{` | Zero or more to zero or more |

## Line Styles

| Syntax | Meaning |
|--------|---------|
| `--` | Identifying relationship (solid line) |
| `..` | Non-identifying relationship (dashed line) |

## Full Example

```mermaid
erDiagram
  DEPARTMENT {
    int id PK
    string name
  }
  EMPLOYEE {
    int id PK
    string first_name
    string last_name
    int department_id FK
    int manager_id FK
  }
  PROJECT {
    int id PK
    string name
    date start_date
    date end_date
  }
  ASSIGNMENT {
    int employee_id FK
    int project_id FK
    string role
    decimal hours
  }
  DEPARTMENT ||--|{ EMPLOYEE : "has"
  EMPLOYEE ||--o| EMPLOYEE : "managed by"
  EMPLOYEE ||--o{ ASSIGNMENT : "works on"
  PROJECT ||--o{ ASSIGNMENT : "assigned to"
```
