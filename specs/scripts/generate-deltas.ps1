#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generate delta entries for a feature showing all file changes.

.DESCRIPTION
    Analyzes Git history to detect ADDED, MODIFIED, REMOVED, and RENAMED files
    for a feature. Outputs delta entries in Markdown or JSON format.

.PARAMETER FeatureDir
    Path to the feature directory to analyze.

.PARAMETER BaseRef
    Git ref to compare against (branch, tag, or commit). Default: "main"

.PARAMETER Strict
    Include diff content and summary for MODIFIED files.

.PARAMETER Json
    Output results in JSON format.

.PARAMETER OutputFile
    Optional. Write output to this file instead of stdout.

.OUTPUTS
    Delta entries in Markdown or JSON format.

.EXAMPLE
    ./generate-deltas.ps1 -FeatureDir "specs/001-feature"
    Lists all deltas for the feature in Markdown format.

.EXAMPLE
    ./generate-deltas.ps1 -FeatureDir "specs/001-feature" -Strict -Json
    Lists deltas with diff content in JSON format.

.NOTES
Exit Codes:
    0 - Success (deltas generated)
    1 - Error (invalid feature directory or git operation failed)
#>

param(
    [Parameter(Mandatory=$True, Position=0)]
    [string]$FeatureDir,

    [string]$BaseRef = "main",

    [switch]$Strict,

    [switch]$Json,

    [string]$OutputFile
)

# Import common functions
$ScriptDir = $PSScriptRoot
. (Join-Path $ScriptDir "common.ps1")

# Validate feature directory
if (-not (Test-Path $FeatureDir)) {
    Write-Error "Feature directory not found: $FeatureDir"
    exit 2
}

# Check Git availability
$HasGit = Test-HasGit
if (-not $HasGit) {
    Write-Warning "[speckit] Git not available - delta detection limited"
    Write-Warning "[speckit] RENAMED detection is disabled without Git"
}

# Get deltas
$Deltas = Get-FileDeltas -BaseRef $BaseRef -FeatureDir $FeatureDir -IncludeDiffContent:$Strict

# Filter by allowed extensions (Task K.12)
$AllowedExtensions = @(
    '.md', '.agent.md', '.prompt.md', '.instructions.md',
    '.ps1', '.json', '.yaml', '.yml'
)
$Deltas = $Deltas | Where-Object {
    $ItemPath = if ($_.Operation -eq "RENAMED") { $_.TargetPath } else { $_.Path }
    $Matched = $False
    foreach ($Ext in $AllowedExtensions) {
        if ($ItemPath.EndsWith($Ext, [System.StringComparison]::OrdinalIgnoreCase)) {
            $Matched = $True
            break
        }
    }
    $Matched
}

# Build output
if ($Json) {
    $FeatureName = Split-Path $FeatureDir -Leaf
    $Output = @{
        feature = $FeatureName
        base_ref = $BaseRef
        timestamp = (Get-Date -Format "o")
        summary = @{
            added = ($Deltas | Where-Object { $_.Operation -eq "ADDED" } | Measure-Object).Count
            modified = ($Deltas | Where-Object { $_.Operation -eq "MODIFIED" } | Measure-Object).Count
            removed = ($Deltas | Where-Object { $_.Operation -eq "REMOVED" } | Measure-Object).Count
            renamed = ($Deltas | Where-Object { $_.Operation -eq "RENAMED" } | Measure-Object).Count
            total = $Deltas.Count
        }
        deltas = $Deltas | ForEach-Object {
            @{
                operation = $_.Operation
                path = $_.Path
                target_path = $_.TargetPath
                diff_summary = $_.DiffSummary
                diff_content = $_.DiffContent
            }
        }
    }

    $JsonOutput = $Output | ConvertTo-Json -Depth 10

    if ($OutputFile) {
        $JsonOutput | Out-File -FilePath $OutputFile -Encoding utf8
        Write-Host "Delta output written to: $OutputFile"
    } else {
        Write-Output $JsonOutput
    }
} else {
    # Markdown format
    $Lines = @()
    $Lines += "## Delta Summary"
    $Lines += ""
    $Lines += "**Feature**: $(Split-Path $FeatureDir -Leaf)"
    $Lines += "**Base Ref**: $BaseRef"
    $Lines += "**Generated**: $(Get-StandardTimestamp)"
    $Lines += ""

    $AddedCount = ($Deltas | Where-Object { $_.Operation -eq "ADDED" } | Measure-Object).Count
    $ModifiedCount = ($Deltas | Where-Object { $_.Operation -eq "MODIFIED" } | Measure-Object).Count
    $RemovedCount = ($Deltas | Where-Object { $_.Operation -eq "REMOVED" } | Measure-Object).Count
    $RenamedCount = ($Deltas | Where-Object { $_.Operation -eq "RENAMED" } | Measure-Object).Count

    $Lines += "| Operation | Count |"
    $Lines += "|-----------|-------|"
    $Lines += "| ADDED | $AddedCount |"
    $Lines += "| MODIFIED | $ModifiedCount |"
    $Lines += "| REMOVED | $RemovedCount |"
    $Lines += "| RENAMED | $RenamedCount |"
    $Lines += "| **Total** | $(if ($Deltas) { $Deltas.Count } else { 0 }) |"
    $Lines += ""
    $Lines += "### File Changes"
    $Lines += ""

    # Format deltas as markdown
    if ($Deltas -and $Deltas.Count -gt 0) {
        $DeltaLines = Format-DeltaMarkdown -Deltas $Deltas
        $Lines += $DeltaLines
    } else {
        $Lines += "_No file changes detected._"
    }

    if (-not $HasGit) {
        $Lines += ""
        $Lines += "> **Note**: Git not available. RENAMED detection was disabled."
    }

    $Output = $Lines -join "`n"

    if ($OutputFile) {
        $Output | Out-File -FilePath $OutputFile -Encoding utf8
        Write-Host "Delta output written to: $OutputFile"
    } else {
        Write-Output $Output
    }
}

exit 0

