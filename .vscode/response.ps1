
To do a **full, repeatable audit** inside your repo, add this script and run it; it will scan text files for referenced paths (Markdown links, `filepath:` markers, quoted/backticked paths, and common `specs/...` / `.github/...` tokens) and report **missing files/folders**.

````powershell
#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Strict,
    [string[]]$Roots = @(".")
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")

$RepoRoot = Get-RepoRoot

function Get-TextFiles {
    param([string]$Base)

    $excludeDirs = @(
        ".git", "node_modules", "dist", "build", "out", "target",
        ".cache", ".next", ".turbo", ".vite", ".agent_work", "coverage",
        "bin", "obj", ".idea", ".vscode"
    )

    $extAllow = @(
        ".md", ".ps1", ".psm1", ".json", ".jsonc", ".yml", ".yaml", ".txt",
        ".js", ".jsx", ".ts", ".tsx", ".cs", ".py", ".java", ".go", ".rb", ".php", ".sh"
    )

    Get-ChildItem -LiteralPath $Base -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $full = $_.FullName
            foreach ($d in $excludeDirs) {
                if ($full -match ([regex]::Escape([IO.Path]::DirectorySeparatorChar + $d + [IO.Path]::DirectorySeparatorChar))) { return $false }
                if ($full -match ([regex]::Escape("/$d/"))) { return $false }
                if ($full -match ([regex]::Escape("\$d\"))) { return $false }
            }
            return $extAllow -contains $_.Extension.ToLowerInvariant()
        }
}

function Normalize-Ref {
    param([string]$Ref)

    if ([string]::IsNullOrWhiteSpace($Ref)) { return $null }

    $r = $Ref.Trim()

    # Strip surrounding wrappers
    $r = $r.Trim("`", "'", '"')

    # Remove trailing punctuation
    $r = $r.TrimEnd(")", "]", "}", ".", ",", ":", ";")

    # Drop anchors/query fragments for file checks
    $hash = $r.IndexOf('#')
    if ($hash -ge 0) { $r = $r.Substring(0, $hash) }
    $q = $r.IndexOf('?')
    if ($q -ge 0) { $r = $r.Substring(0, $q) }

    $r = $r.Trim()

    if ([string]::IsNullOrWhiteSpace($r)) { return $null }

    # Ignore obvious URLs and mailto
    if ($r -match '^(https?|mailto):') { return $null }

    return $r
}

function Resolve-RefPath {
    param([string]$Ref)

    $r = Normalize-Ref $Ref
    if (-not $r) { return $null }

    # Absolute?
    if ([IO.Path]::IsPathRooted($r)) {
        return [PSCustomObject]@{
            Ref      = $r
            Resolved = $r
        }
    }

    # Relative to repo root
    $resolved = Join-Path $RepoRoot $r
    return [PSCustomObject]@{
        Ref      = $r
        Resolved = $resolved
    }
}

function Test-RefExists {
    param([string]$Path)

    if (-not $Path) { return $false }

    # Try exact, then try normalized separators
    if (Test-Path -LiteralPath $Path) { return $true }

    $alt = $Path -replace '/', '\'
    if (Test-Path -LiteralPath $alt) { return $true }

    $alt2 = $Path -replace '\\', '/'
    if (Test-Path -LiteralPath $alt2) { return $true }

    return $false
}

$rootsAbs = @()
foreach ($r in $Roots) {
    $p = if ([IO.Path]::IsPathRooted($r)) { $r } else { Join-Path $RepoRoot $r }
    $rootsAbs += $p
}

$files = @()
foreach ($r in $rootsAbs) {
    if (Test-Path -LiteralPath $r -PathType Container) {
        $files += Get-TextFiles -Base $r
    }
}

$occurrences = New-Object System.Collections.Generic.List[object]

# Regexes: markdown links, ref-style, filepath markers, and path-like tokens
$rxMdLink = [regex]'\]\((?<p>[^)]+)\)'
$rxMdRef  = [regex]'^\[(?<id>[^\]]+)\]:\s*(?<p>\S+)\s*$'
$rxFilepathMarker = [regex]'filepath:\s*(?<p>.+)$'
$rxPathToken = [regex]'(?<p>(?:\.github|specs|src|tests|docs)[\\/][A-Za-z0-9._\-\\/]+(?:\.[A-Za-z0-9]+)?)'
$rxQuotedOrTicked = [regex]'(?<q>["''`])(?<p>[^"''`\r\n]{2,}?[\\/][^"''`\r\n]{2,}?)\k<q>'

foreach ($f in $files) {
    $rel = $f.FullName.Substring($RepoRoot.Length).TrimStart('\','/')
    $lines = Get-Content -LiteralPath $f.FullName -ErrorAction SilentlyContinue

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        foreach ($m in $rxMdLink.Matches($line)) {
            $refObj = Resolve-RefPath $m.Groups['p'].Value
            if ($refObj) {
                $occurrences.Add([PSCustomObject]@{
                    source = $rel; line = $i + 1; raw = $m.Groups['p'].Value
                    normalized = $refObj.Ref; resolved = $refObj.Resolved
                })
            }
        }

        $m2 = $rxMdRef.Match($line)
        if ($m2.Success) {
            $refObj = Resolve-RefPath $m2.Groups['p'].Value
            if ($refObj) {
                $occurrences.Add([PSCustomObject]@{
                    source = $rel; line = $i + 1; raw = $m2.Groups['p'].Value
                    normalized = $refObj.Ref; resolved = $refObj.Resolved
                })
            }
        }

        $m3 = $rxFilepathMarker.Match($line)
        if ($m3.Success) {
            $refObj = Resolve-RefPath $m3.Groups['p'].Value
            if ($refObj) {
                $occurrences.Add([PSCustomObject]@{
                    source = $rel; line = $i + 1; raw = $m3.Groups['p'].Value
                    normalized = $refObj.Ref; resolved = $refObj.Resolved
                })
            }
        }

        foreach ($m in $rxQuotedOrTicked.Matches($line)) {
            $refObj = Resolve-RefPath $m.Groups['p'].Value
            if ($refObj) {
                $occurrences.Add([PSCustomObject]@{
                    source = $rel; line = $i + 1; raw = $m.Groups['p'].Value
                    normalized = $refObj.Ref; resolved = $refObj.Resolved
                })
            }
        }

        foreach ($m in $rxPathToken.Matches($line)) {
            $refObj = Resolve-RefPath $m.Groups['p'].Value
            if ($refObj) {
                $occurrences.Add([PSCustomObject]@{
                    source = $rel; line = $i + 1; raw = $m.Groups['p'].Value
                    normalized = $refObj.Ref; resolved = $refObj.Resolved
                })
            }
        }
    }
}

# De-dup occurrences (same source+line+normalized)
$occurrences = $occurrences |
    Sort-Object source, line, normalized -Unique

# Evaluate existence
$evaluated = $occurrences | ForEach-Object {
    $exists = Test-RefExists -Path $_.resolved
    [PSCustomObject]@{
        source     = $_.source
        line       = $_.line
        raw        = $_.raw
        normalized = $_.normalized
        resolved   = $_.resolved
        exists     = $exists
    }
}

$missing = $evaluated | Where-Object { -not $_.exists }

$summary = [PSCustomObject]@{
    repo_root          = $RepoRoot
    scanned_files      = $files.Count
    reference_hits     = $evaluated.Count
    missing_hits       = $missing.Count
    missing_unique     = ($missing | Select-Object -ExpandProperty normalized | Sort-Object -Unique).Count
}

if ($Json) {
    @{
        summary   = $summary
        missing   = $missing
        evaluated = $evaluated
    } | ConvertTo-Json -Depth 6 -Compress
    if ($Strict -and $missing.Count -gt 0) { exit 1 }
    exit 0
}

Write-Host "[speckit] Reference Audit" -ForegroundColor Cyan
Write-Host "========================"
Write-Host "Repo Root: $RepoRoot"
Write-Host "Scanned Files: $($summary.scanned_files)"
Write-Host "Reference Hits: $($summary.reference_hits)"
Write-Host "Missing Hits: $($summary.missing_hits)"
Write-Host "Missing Unique: $($summary.missing_unique)"
Write-Host ""

if ($missing.Count -eq 0) {
    Write-Host "✓ No missing referenced paths detected." -ForegroundColor Green
    exit 0
}

Write-Host "Missing referenced paths (grouped):" -ForegroundColor Yellow
$missing |
    Group-Object normalized |
    Sort-Object Count -Descending |
    ForEach-Object {
        $norm = $_.Name
        $count = $_.Count
        $sample = $_.Group | Select-Object -First 3
        Write-Host ""
        Write-Host "- $norm ($count occurrence(s))" -ForegroundColor Red
        foreach ($s in $sample) {
            Write-Host "  - $($s.source):$($s.line)  ->  $($s.resolved)"
        }
    }

if ($Strict) { exit 1 }
````

### Run it (from repo root)

````pwsh
pwsh specs/scripts/audit-references.ps1
````

Optional machine-readable output:

````pwsh
pwsh specs/scripts/audit-references.ps1 -Json | jq .
````

This script reuses your existing repo-root detection from `Get-RepoRoot` in common.ps1.
