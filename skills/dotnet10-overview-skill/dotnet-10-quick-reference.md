# .NET 10 Quick Reference Guide

## Release Information at a Glance

| Property | Value |
|----------|-------|
| **Version** | .NET 10 |
| **Release Date** | November 11, 2025 |
| **Release Type** | Long Term Support (LTS) |
| **Support Until** | November 10, 2028 |
| **Download URL** | https://get.dot.net/10 |

---

## C# 14 Quick Syntax

### Field-Backed Properties
```csharp
// Before: Explicit backing field
private string _name;
public string Name
{
    get => _name;
    set => _name = value;
}

// After: Automatic field-backed property
public string Name { get; set; }
```

### Extension Properties
```csharp
// Add properties to types you don't own
public static class StringExtensions
{
    public static int WordCount { get; } // Now supported
}
```

### Null-Conditional Assignment
```csharp
// Simplified null-safe assignment
obj?.Property ??= defaultValue;
```

---

## Feature Categories

### Performance (Runtime Level)
- JIT compiler optimizations
- AVX10.2 & Arm64 SVE hardware support
- NativeAOT smaller binaries
- 8-20% GC pause time reduction on Arm64

### Developer Experience
- New C# 14 syntax features
- F# 10 refinements
- Improved tooling (Visual Studio 2026, C# Dev Kit)

### Modern Architecture
- Microsoft Agent Framework
- Model Context Protocol (MCP)
- Microsoft.Extensions.AI unified abstractions

### Web & APIs
- Passkey authentication
- ASP.NET Core memory improvements
- Blazor state persistence & circuit resilience

### Data
- SQL Server 2025 vector search
- Native JSON data type support
- Complex type modeling

---

## When to Use .NET 10

✅ **Ideal for:**
- Enterprise applications requiring 3-year support
- AI/ML integration projects
- High-performance systems
- Modern web applications
- Vector/semantic search applications

---

## Coordinated Releases

All of the following were released simultaneously with .NET 10:
- Visual Studio 2026
- C# Dev Kit
- Supporting tools and libraries

---

## Key Improvements by Category

### Productivity ⚡
- Reduced boilerplate with field-backed properties
- Extension properties for external types
- Better async patterns

### Security 🔒
- Passkey authentication support
- Modern cryptographic standards
- Secure by default patterns

### Performance 🚀
- Smaller NativeAOT binaries
- Faster JIT compilation
- Optimized memory management
- Hardware acceleration support

### Intelligence 🧠
- Microsoft Agent Framework
- Unified AI abstractions
- MCP protocol support
- Semantic search capabilities

---

## Migration Considerations

- LTS release ensures production stability
- 3-year support window provides planning flexibility
- Most apps can upgrade without major breaking changes
- Modern C# features are opt-in

---

## Community & Support

- Part of the .NET ecosystem evolution
- Continues .NET's performance focus
- Integrates latest AI/ML standards
- Builds on previous LTS releases (similar to .NET Framework)
