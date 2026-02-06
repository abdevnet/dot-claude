# Sequence Diagrams

## Basics

```mermaid
sequenceDiagram
  participant A as Alice
  participant B as Bob
  A->>B: Hello Bob!
  B-->>A: Hi Alice!
```

## Participant Types

- `participant A as Alice` — renders as a box
- `actor A as Alice` — renders as a stick figure

Participants appear in declaration order left-to-right.

## Arrow Types

| Syntax | Line | Arrowhead |
|--------|------|-----------|
| `->>` | Solid | Filled |
| `-->>` | Dashed | Filled |
| `-)` | Solid | Open |
| `--)` | Dashed | Open |

## Activation (Lifelines)

Use `+` to activate and `-` to deactivate:

```mermaid
sequenceDiagram
  participant Client
  participant Server
  Client->>+Server: Request
  Server-->>-Client: Response
```

## Self-Messages

A participant can send a message to itself:

```mermaid
sequenceDiagram
  participant A as Service
  A->>A: Internal processing
```

## Blocks

### Loop
```mermaid
sequenceDiagram
  participant A
  participant B
  loop Every 5 seconds
    A->>B: Health check
    B-->>A: OK
  end
```

### Alt/Else (Conditional)
```mermaid
sequenceDiagram
  participant A as Client
  participant B as Server
  A->>B: Request
  alt Success
    B-->>A: 200 OK
  else Failure
    B-->>A: 500 Error
  end
```

### Opt (Optional)
```mermaid
sequenceDiagram
  participant A
  participant B
  opt Cache available
    A->>B: Return cached data
  end
```

### Par (Parallel)
```mermaid
sequenceDiagram
  participant A as Gateway
  participant B as Service1
  participant C as Service2
  par Request to Service1
    A->>B: Fetch user
  and Request to Service2
    A->>C: Fetch orders
  end
  B-->>A: User data
  C-->>A: Order data
```

### Critical
```mermaid
sequenceDiagram
  critical Establish connection
    A->>B: Connect
    B-->>A: Connected
  end
```

### Break
```mermaid
sequenceDiagram
  participant A
  participant B
  A->>B: Request
  break When rate limited
    B-->>A: 429 Too Many Requests
  end
  B-->>A: 200 OK
```

## Notes

```mermaid
sequenceDiagram
  participant A
  participant B
  Note left of A: Client-side
  Note right of B: Server-side
  Note over A,B: Shared context
  A->>B: Request
```
