# GitHub Copilot Custom Instructions for Swank Motion Pictures

## General Guidelines

- Use `Id` for PascalCase and `id` for camelCase.
- Prefer readability over conciseness. If a one-liner is unclear, split it into multiple statements.
- Use C# aliases (`int`, `string`, etc.) rather than .NET types (`Int32`, `String`) unless a specific type is necessary.
- Curly braces `{}` should appear on a new line.
- File names should match class names; avoid multiple classes per file.
- Use `string.Empty` instead of `""`.
- Prefer `StringBuilder` for long string manipulations.
- Use generic collections over non-generic ones (`List<T>` over `ArrayList`).
- Remove unused `using` directives.
- Ensure files conform to "Resharper Green" best practices.

## Naming Conventions

### Classes, Methods, and Properties
- Use PascalCase for class, method, and property names.
- Use camelCase with an underscore prefix (`_`) for private fields.
- Include access specifiers on all members.
- Name methods with a verb-object structure (e.g., `ShowDialog()`).
- Async methods should be suffixed with `Async` (except in WPF/WinForms event handlers).

```csharp
public class MyClass : IMyInterface, INotifyPropertyChanged
{
    private int _swankId;
    
    public MyClass()
    {
    }
    
    public int SwankId
    {
        get { return _swankId; }
        set
        {
            _swankId = value;
            OnNotifyPropertyChanged(nameof(SwankId));
        }
    }
    
    public void UpdateSwankIdLastModifieds()
    {
    }
}
```

### Local Variables and Method Arguments
- Use camelCase.

```csharp
void MyMethod(int someNumber)
{
    int isThisNumberEven;
}
```

### Interfaces
- Prefix interfaces with `I`.
- Name interfaces using nouns (`IComponent`), noun phrases (`ICustomAttributeProvider`), or adjectives (`IPersistable`).
- Default implementations should match the interface name (`DefaultTranscodeProcessor` for `ITranscodeProcessor`).

```csharp
public interface ITranscodeProcessor
{
}
```

### Private Fields
- Prefix private fields with `_` and use camelCase.
- Avoid public fields; prefer properties.

```csharp
public class MyClass
{
    private int _swankId;
}
```

## Custom Classes
### Attribute Classes
- Suffix custom attribute classes with `Attribute`.

### Exception Classes
- Suffix custom exception classes with `Exception`.

## Exception Handling
- Avoid empty `catch` blocks. If necessary, discuss justification.
- Catch and log specific exceptions where possible.
- Use `throw;` instead of `throw e;` when re-throwing exceptions.
- Prefer .NET standard exception types and use the most specific applicable exception.
- Provide properties that allow users to detect potential exceptions before they occur.

## `var` Usage
- Use `var` only when the type is evident from the assignment.

```csharp
var i = 25;
var myString = "Hello World!";
var o = new FilmInformation();
```

- Avoid `var` where the type is ambiguous.

```csharp
var result = o.ProcessFilmNumber(filmNumber);
var foo = o.GetNextJobDetail();
```

## XML Documentation
- Document all non-private types, methods, fields, events, and delegates.
- Use XML documentation tags to improve IntelliSense and support automated documentation generation.

### Section Tags

| Tag        | Description                                         | Applies To |
|------------|-----------------------------------------------------|------------|
| `<summary>`  | Short description                                   | Type or member |
| `<remarks>`  | Additional information and preconditions         | Type or member |
| `<param>`    | Describes method parameters                      | Method |
| `<returns>`  | Describes the return value of a method           | Method |
| `<exception>` | Lists potential exceptions thrown               | Method, event, or property |
| `<value>`    | Describes a property's accepted/returned type   | Property |
| `<example>`  | Provides usage examples                         | Type or member |
| `<seealso>`  | Adds a reference in the "See Also" section     | Type or member |
| `<overloads>`| Summarizes method overloads                     | First method in an overload list |

### Inline Tags
- `<see>`: Creates a hyperlink to another member or type.
- `<paramref>`: References a method parameter.

### Formatting Tags
- `<code>`: Formats code blocks.
- `<c>`: Displays text in a fixed-width font (often used with `<code>`).
- `<para>`: Creates a new paragraph.
- `<list>`: Creates a bulleted/numbered list or a table.
- `<b>`: Bold text.
- `<i>`: Italic text.

#### Exception:
- In an inheritance hierarchy, use `<see>` to refer to the base class or interface and `<inheritdoc>` instead of repeating documentation.

---

By following these guidelines, GitHub Copilot will generate C# code that aligns with our company's best practices.