# Class Diagrams

## Basics

```mermaid
classDiagram
  class Animal {
    +int age
    +String gender
    +isMammal() bool
    +mate()
  }
  class Duck {
    +String beakColor
    +swim()
    +quack()
  }
  Animal <|-- Duck
```

## Visibility Markers

| Marker | Meaning |
|--------|---------|
| `+` | Public |
| `-` | Private |
| `#` | Protected |
| `~` | Package/internal |

## Member Modifiers

- Static: append `$` → `+staticMethod()$`
- Abstract: append `*` → `+abstractMethod()*`

## Return Types

```
+getAge() int
+setName(String name) void
```

## Annotations

```mermaid
classDiagram
  class IFlyable {
    <<interface>>
    +fly() void
  }
  class Shape {
    <<abstract>>
    +area() double*
  }
  class Color {
    <<enumeration>>
    RED
    GREEN
    BLUE
  }
```

## Generics

```mermaid
classDiagram
  class List~T~ {
    +add(T item) void
    +get(int index) T
  }
```

## Inline Attributes

```mermaid
classDiagram
  Customer : +String name
  Customer : +String email
  Customer : +placeOrder()
```

## Relationships

| Type | Syntax | Marker |
|------|--------|--------|
| Inheritance | `<\|--` | Hollow triangle |
| Composition | `*--` | Filled diamond |
| Aggregation | `o--` | Hollow diamond |
| Association | `-->` | Open arrow |
| Dependency | `..>` | Dashed open arrow |
| Realization | `..\|>` | Dashed hollow triangle |

### With Cardinality and Labels

```mermaid
classDiagram
  Customer "1" --> "*" Order : places
  Order "1" *-- "1..*" LineItem : contains
  Order "1" --> "1" Payment : paid by
```

## Namespaces

```mermaid
classDiagram
  namespace Domain {
    class Order {
      +int id
      +submit()
    }
    class Customer {
      +String name
    }
  }
  namespace Infrastructure {
    class OrderRepository {
      +save(Order) void
    }
  }
  OrderRepository ..> Order
```

## Direction

Default is top-down. Use `direction` to change:

```mermaid
classDiagram
  direction LR
  Animal <|-- Duck
  Animal <|-- Fish
```
