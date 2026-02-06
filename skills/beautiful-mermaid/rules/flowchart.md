# Flowcharts & State Diagrams

## Flowchart Basics

Start with `graph` or `flowchart` followed by a direction:

| Direction | Meaning |
|-----------|---------|
| `TD` / `TB` | Top to bottom |
| `LR` | Left to right |
| `BT` | Bottom to top |
| `RL` | Right to left |

```mermaid
graph TD
  A[Start] --> B{Decision}
  B -->|Yes| C[Process]
  B -->|No| D[End]
  C --> D
```

## Node Shapes

| Shape | Syntax | Use for |
|-------|--------|---------|
| Rectangle | `A[text]` | Default/process |
| Rounded | `A(text)` | Soft/general |
| Diamond | `A{text}` | Decision |
| Stadium | `A([text])` | Terminal/pill |
| Circle | `A((text))` | Events |
| Subroutine | `A[[text]]` | Predefined process |
| Double Circle | `A(((text)))` | Double event |
| Hexagon | `A{{text}}` | Preparation |
| Cylinder | `A[(text)]` | Database/storage |
| Asymmetric | `A>text]` | Flag/input |
| Trapezoid | `A[/text\]` | Manual operation |
| Inv Trapezoid | `A[\text/]` | Manual operation alt |

## Edge Types

| Type | Syntax | Appearance |
|------|--------|------------|
| Solid arrow | `-->` | ——▶ |
| Dotted arrow | `-.->` | - - ▶ |
| Thick arrow | `==>` | ══▶ |
| No arrow | `---` | —— |
| Dotted no arrow | `-.-` | - - - |
| Thick no arrow | `===` | ═══ |
| Bidirectional | `<-->` | ◀——▶ |
| Dotted bidirectional | `<-.->` | ◀- -▶ |
| Thick bidirectional | `<==>` | ◀══▶ |

### Edge Labels

```mermaid
graph LR
  A -->|label text| B
  C -- label text --> D
```

### Parallel Links with `&`

```mermaid
graph TD
  A & B --> C & D
```

### Chained Edges

```mermaid
graph LR
  A --> B --> C --> D
```

## Subgraphs

Group related nodes:

```mermaid
graph TD
  subgraph Backend [Backend Services]
    direction LR
    api[API Gateway] --> auth[Auth Service]
    api --> data[Data Service]
  end
  subgraph Frontend [Frontend Apps]
    web[Web App]
    mobile[Mobile App]
  end
  web --> api
  mobile --> api
```

- Use `direction` inside a subgraph to override layout
- Bracket syntax `subgraph id [Label]` sets the display label
- Subgraphs can be nested

## Styling

### Class Definitions

```mermaid
graph TD
  classDef primary fill:#3b82f6,stroke:#1d4ed8,color:#fff
  classDef danger fill:#ef4444,stroke:#b91c1c,color:#fff
  A[Normal]:::primary --> B[Alert]:::danger
```

### Inline Styles

```mermaid
graph TD
  A[Styled Node]
  style A fill:#f9f,stroke:#333,color:#000
```

## State Diagrams

Use `stateDiagram-v2` for state machines:

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Processing : start
  Processing --> Complete : done
  Processing --> Error : fail
  Error --> Idle : retry
  Complete --> [*]
```

- `[*]` at start = initial state (filled circle)
- `[*]` at end = final state (bullseye)
- `state "Description" as alias` for long names
- Composite states with `state CompositeState { ... }`

```mermaid
stateDiagram-v2
  state Active {
    [*] --> Running
    Running --> Paused : pause
    Paused --> Running : resume
  }
  [*] --> Active
  Active --> [*] : stop
```
