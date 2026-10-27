#!/usr/bin/env bash
# Prints which standards' signals a diff contains, so the reviewer knows what to load.
# Usage, from inside the repository: standards-signals.sh <base> [<head>]
set -euo pipefail
base="${1:?usage: standards-signals.sh <base> [<head>]}"
head="${2:-HEAD}"
diff=$(git diff --unified=0 --no-color "$base...$head")

check() {
  local label="$1" pattern="$2" file="$3" n
  n=$(printf '%s\n' "$diff" | grep -c -E "$pattern" || true)
  [ "$n" -gt 0 ] && printf '%-30s %5s  %s\n' "$label" "$n" "$file"
  return 0
}

printf '%-30s %5s  %s\n' "signal" "hits" "load"
check "C# files"                '^\+\+\+ b/.*\.cs$'                                   csharp-instructions.md
check "Angular files"           '^\+\+\+ b/.*\.(ts|html|scss)$'                       angular-instructions.md
check "Angular specs"           '^\+\+\+ b/.*\.spec\.ts$'                             angular-testing-instructions.md
check "C# tests"                '^\+\+\+ b/.*(Tests?\.cs$|\.Tests/)'                  csharp-testing-instructions.md
check "Acceptance tests"        'AcceptanceTest|Swank\.AcceptanceTesting'              acceptance-testing-instructions.md
check "SQL text"                '(SELECT|INSERT|UPDATE|DELETE|MERGE|EXEC) '           sqlserver-instructions.md
check "Data access"             'Repository|IDbConnectionWrapper|Dapper|QueryAsync|ExecuteAsync|DbContext' data-instructions.md
check "ASP.NET Core"            '\[ApiController\]|SwankWebApplication|WebApplication|IEndpointRouteBuilder|ProblemDetails|HybridCache|AddAuthentication' aspnetcore-instructions.md
check "SwankResult"             'SwankResult'                                          swankresult-instructions.md
check "HTTP client (C#; Angular HttpClient also matches)" 'HttpClient|IHttpClientFactory|AddHttpClient|Swank\.Web\.Client|DelegatingHandler' httpclient-instructions.md
check "Console or service app"  'SingleRunConsoleApplication|WindowsServiceApplication|IApplicationService|IHostedService|BackgroundService' console-application-instructions.md
check "Product Publicity API"   'ProductPublicity'                                     productpublicityapi-instructions.md
check "appsettings changed"     '^\+\+\+ b/.*appsettings.*\.json$'                    'csharp-instructions.md (csproj nesting rule)'
echo "always: code-review-lenses-instructions.md, comments-instructions.md. Documentation pass: documentation-accuracy-instructions.md."
