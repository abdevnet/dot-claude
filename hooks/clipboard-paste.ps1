#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json

if ($payload.prompt -notmatch '(?i)\bpaste\b') { exit 0 }

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($null -eq $img) {
    [Console]::Error.WriteLine('[clipboard-paste] trigger word matched but no image on clipboard')
    exit 0
}

$dir = Join-Path $env:USERPROFILE '.claude\clipboard'
[void](New-Item -ItemType Directory -Force -Path $dir)
$file = Join-Path $dir ("clip_{0}.png" -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))

$img.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()

Get-ChildItem $dir -Filter 'clip_*.png' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force -ErrorAction SilentlyContinue

@"
[clipboard-paste hook] The user pasted a clipboard image to: $file
You MUST call the Read tool on that exact path before responding, so the image becomes visible to you. Treat the image as primary context for the user's prompt.
"@
