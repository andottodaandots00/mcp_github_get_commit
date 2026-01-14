#!/usr/bin/env pwsh
# Create a new feature for SpecKit Consolidated
# Updated paths for consolidated folder structure (specs/changes/)
#
# CORRECTED VERSION - Fixes from 2ndanalysis.md Issue #3
# Added error handling, rollback logic, and eliminated code duplication
#
# Changes made:
# - Added try-catch blocks around all critical operations
# - Added rollback logic for failed spec creation
# - Removed duplicate root detection logic (now sources from common.ps1 via Get-RepositoryRoot)
# - Added -ErrorAction Stop to all New-Item and Copy-Item calls
# - Added cleanup of branch if directory creation fails
# - Added validation before setting environment variables
# - Added better error messages for debugging
#
# EXIT CODES:
#   0 - Success (feature created)
#   1 - Error (validation failed, directory creation failed, or rollback occurred)

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $True, Position = 0)]
    [string[]]$FeatureDescription,

    [switch]$Json,
    [string]$ShortName,
    [int]$Number = 0,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Host "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] [-Number N] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for the branch"
    Write-Host "  -Number N           Specify branch number manually (overrides auto-detection)"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth'"
    Write-Host "  ./create-new-feature.ps1 'Implement OAuth2 integration for API'"
    exit 0
}

# Check if feature description provided
if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] [-ShortName <name>] <feature description>"
    exit 1
}

$FeatureDesc = ($FeatureDescription -join ' ').Trim()

# NEW: Source common.ps1 for shared functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CommonScript = Join-Path $ScriptDir "common.ps1"

if (-not (Test-Path $CommonScript)) {
    Write-Error "Required file not found: $CommonScript"
    exit 1
}

try {
    . $CommonScript
}
catch {
    Write-Error "Failed to source common.ps1: $_"
    exit 1
}

# NEW: Use Get-RepositoryRoot from common.ps1 instead of duplicate logic
try {
    $RepoRoot = Get-RepositoryRoot
    if (-not $RepoRoot) {
        throw "Could not determine repository root"
    }
}
catch {
    Write-Error "Error: Could not determine repository root. Error: $_"
    exit 1
}

# NEW: Use Test-HasGit from common.ps1
$HasGit = Test-HasGit

Set-Location $RepoRoot

$SpecsDir = Join-Path $RepoRoot 'specs'
$ChangesDir = Join-Path $SpecsDir 'changes'

try {
    New-Item -ItemType Directory -Path $ChangesDir -Force -ErrorAction Stop | Out-Null
}
catch {
    Write-Error "Failed to create changes directory: $ChangesDir. Error: $_"
    exit 1
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)

    $Highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            if ($_.Name -match '^(\d+)') {
                $Num = [int]$Matches[1]
                if ($Num -gt $Highest) { $Highest = $Num }
            }
        }
    }
    return $Highest
}

function Get-HighestNumberFromBranches {
    param()

    $Highest = 0
    try {
        $Branches = git branch -a 2>$Null
        if ($LASTEXITCODE -eq 0) {
            foreach ($Branch in $Branches) {
                $CleanBranch = $Branch.Trim() -replace '^\*?\s+', '' -replace '^remotes/[^/]+/', ''
                # Updated regex to match numbers anywhere in branch name (Issue #29)
                # Matches digit sequences separated by delimiters or at string boundaries
                if ($CleanBranch -match '(?:^|[/-])(\d+)(?:[/-]|$)') {
                    $Num = [int]$Matches[1]
                    if ($Num -gt $Highest) { $Highest = $Num }
                }
            }
        }
    }
    catch {
        Write-Verbose "Could not check Git branches: $_"
    }
    return $Highest
}

function Get-NextBranchNumber {
    param([string]$RepoRoot)

    try {
        git fetch --all --prune 2>$Null | Out-Null
    }
    catch { }

    $HighestBranch = Get-HighestNumberFromBranches
    $HighestSpec = [Math]::Max(
        (Get-HighestNumberFromSpecs -SpecsDir (Join-Path $RepoRoot "specs")),
        (Get-HighestNumberFromSpecs -SpecsDir (Join-Path $RepoRoot "specs" "changes"))
    )

    $MaxNum = [Math]::Max($HighestBranch, $HighestSpec)
    return $MaxNum + 1
}

function ConvertTo-CleanBranchName {
    param([string]$Name)
    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}

function Get-BranchName {
    param([string]$Description)

    $StopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )

    $CleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $Words = $CleanName -split '\s+' | Where-Object { $_ }

    $MeaningfulWords = @()
    foreach ($Word in $Words) {
        if ($StopWords -contains $Word) { continue }
        if ($Word.Length -ge 3) {
            $MeaningfulWords += $Word
        }
        elseif ($Description -match "\b$($Word.ToUpper())\b") {
            $MeaningfulWords += $Word
        }
    }

    if ($MeaningfulWords.Count -gt 0) {
        $MaxWords = if ($MeaningfulWords.Count -eq 4) { 4 } else { 3 }
        $Result = ($MeaningfulWords | Select-Object -First $MaxWords) -join '-'
        return $Result
    }
    else {
        $Result = ConvertTo-CleanBranchName -Name $Description
        $FallbackWords = ($Result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $FallbackWords)
    }
}

# Generate branch name
if ($ShortName) {
    $BranchSuffix = ConvertTo-CleanBranchName -Name $ShortName
}
else {
    $BranchSuffix = Get-BranchName -Description $FeatureDesc
}

# Determine branch number
if ($Number -eq 0) {
    if ($HasGit) {
        $Number = Get-NextBranchNumber -RepoRoot $RepoRoot
    }
    else {
        $Number = (Get-HighestNumberFromSpecs -SpecsDir $ChangesDir) + 1
    }
}

$FeatureNum = ('{0:000}' -f $Number)
$BranchName = "$FeatureNum-$BranchSuffix"

# Validate branch name length
$MaxBranchLength = 244
if ($BranchName.Length -gt $MaxBranchLength) {
    $MaxSuffixLength = $MaxBranchLength - 4
    $TruncatedSuffix = $BranchSuffix.Substring(0, [Math]::Min($BranchSuffix.Length, $MaxSuffixLength))
    $TruncatedSuffix = $TruncatedSuffix -replace '-$', ''
    $OriginalBranchName = $BranchName
    $BranchName = "$FeatureNum-$TruncatedSuffix"
    Write-Warning "[speckit] Branch name exceeded 244-byte limit, truncated to: $BranchName"
}

# NEW: Track if branch was created for rollback purposes
$BranchCreated = $False
$FeatureDir = Join-Path $ChangesDir $BranchName

# NEW: Create branch with proper error handling
if ($HasGit) {
    try {
        # Check if branch already exists
        $ExistingBranch = git rev-parse --verify $BranchName 2>$Null
        if ($LASTEXITCODE -eq 0) {
            Write-Error "Branch '$BranchName' already exists. Please choose a different name or number."
            exit 1
        }

        git checkout -b $BranchName 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Git checkout failed with exit code: $LASTEXITCODE"
        }
        $BranchCreated = $True
        Write-Verbose "Created git branch: $BranchName"
    }
    catch {
        Write-Error "Failed to create git branch '$BranchName': $_"
        exit 1
    }
}
else {
    Write-Warning "[speckit] Warning: Git repository not detected; skipped branch creation for $BranchName"
}

# NEW: Create feature directory with rollback on failure
try {
    if (Test-Path $FeatureDir) {
        throw "Feature directory already exists: $FeatureDir"
    }

    New-Item -ItemType Directory -Path $FeatureDir -Force -ErrorAction Stop | Out-Null
    Write-Verbose "Created feature directory: $FeatureDir"
}
catch {
    Write-Error "Failed to create feature directory: $FeatureDir. Error: $_"

    # NEW: Rollback - delete branch if it was created
    if ($BranchCreated -and $HasGit) {
        Write-Warning "Rolling back: deleting branch '$BranchName'..."
        try {
            git checkout main 2>$Null | Out-Null
            git branch -D $BranchName 2>$Null | Out-Null
            Write-Host "Branch '$BranchName' deleted." -ForegroundColor Yellow
        }
        catch {
            Write-Warning "Could not delete branch '$BranchName'. Manual cleanup may be required."
        }
    }

    exit 1
}

# NEW: Copy template with error handling and rollback
$Template = Join-Path $SpecsDir 'templates' 'spec-template.md'
$SpecFile = Join-Path $FeatureDir 'spec.md'

try {
    if (Test-Path $Template) {
        Copy-Item $Template $SpecFile -Force -ErrorAction Stop
        Write-Verbose "Copied template to: $SpecFile"

        # Replace header metadata placeholders only; content placeholders filled by AI agents
        if (Test-Path $SpecFile) {
            $SpecContent = Get-Content $SpecFile -Raw -Encoding UTF8

            # Derive values for placeholder replacement
            $CreatedDate = Get-Date -Format 'yyyy-MM-dd'
            $IssueNumber = $FeatureNum  # Already formatted as "001", "002", etc.
            $FeatureName = $BranchSuffix
            $FeatureDescription = if ($ShortName) { $ShortName } else { $FeatureDesc }

            # Replace only valid header placeholders (escape special regex chars in replacement)
            $EscapedFeatureDesc = $FeatureDescription -replace '\$', '$$'
            $EscapedFeatureName = $FeatureName -replace '\$', '$$'
            $EscapedOriginalRequest = $FeatureDesc -replace '\$', '$$'

            # Header metadata replacements (5 valid placeholders)
            $SpecContent = $SpecContent -replace '\{FEATURE_NAME\}', $EscapedFeatureDesc
            $SpecContent = $SpecContent -replace '\{FEATURE-NAME\}', $EscapedFeatureName
            $SpecContent = $SpecContent -replace '\{ISSUE-NUMBER\}', $IssueNumber
            $SpecContent = $SpecContent -replace '\{YYYY-MM-DD\}', $CreatedDate
            $SpecContent = $SpecContent -replace '\{ORIGINAL_USER_REQUEST\}', $EscapedOriginalRequest

            # Optional: Replace STORY_TITLE with feature description for convenience
            $SpecContent = $SpecContent -replace '\{STORY_TITLE\}', $EscapedFeatureDesc

            Set-Content -Path $SpecFile -Value $SpecContent -Encoding UTF8 -NoNewline
            Write-Verbose "Replaced header metadata placeholders in spec file"
        }
    }
    else {
        Write-Warning "Template not found: $Template. Creating empty spec file."
        New-Item -ItemType File -Path $SpecFile -ErrorAction Stop | Out-Null
    }
}
catch {
    Write-Error "Failed to create spec file: $SpecFile. Error: $_"

    # NEW: Rollback - delete directory and branch
    Write-Warning "Rolling back: cleaning up feature directory and branch..."

    if (Test-Path $FeatureDir) {
        try {
            Remove-Item -Path $FeatureDir -Recurse -Force -ErrorAction Stop
            Write-Verbose "Removed feature directory: $FeatureDir"
        }
        catch {
            Write-Warning "Could not remove feature directory: $FeatureDir"
        }
    }

    if ($BranchCreated -and $HasGit) {
        try {
            git checkout main 2>$Null | Out-Null
            git branch -D $BranchName 2>$Null | Out-Null
            Write-Host "Branch '$BranchName' deleted." -ForegroundColor Yellow
        }
        catch {
            Write-Warning "Could not delete branch '$BranchName'. Manual cleanup may be required."
        }
    }

    exit 1
}

# NEW: Validate before setting environment variables
if (-not (Test-Path $SpecFile)) {
    Write-Error "Spec file was not created successfully: $SpecFile"
    exit 1
}

# NEW (T060): Update project.md with new feature entry
$PopulateScript = Join-Path $ScriptDir "populate-project.ps1"
if (Test-Path $PopulateScript) {
    try {
        & $PopulateScript -Action add -FeatureBranch $BranchName -ErrorAction SilentlyContinue
        Write-Verbose "Updated project.md with new feature entry"
    } catch {
        Write-Verbose "Could not update project.md: $_"
        # Non-fatal - continue with feature creation
    }
} else {
    Write-Verbose "populate-project.ps1 not found - skipping project.md update"
}

# Set environment variable for the current session
$Env:SPECIFY_CHANGE_ID = $BranchName

if ($Json) {
    $Obj = [PSCustomObject]@{
        BRANCH_NAME = $BranchName
        SPEC_FILE   = $SpecFile
        FEATURE_NUM = $FeatureNum
        FEATURE_DIR = $FeatureDir
        HAS_GIT     = $HasGit
        SUCCESS     = $True
    }
    $Obj | ConvertTo-Json -Compress
}
else {
    Write-Output "BRANCH_NAME: $BranchName"
    Write-Output "SPEC_FILE: $SpecFile"
    Write-Output "FEATURE_DIR: $FeatureDir"
    Write-Output "FEATURE_NUM: $FeatureNum"
    Write-Output "HAS_GIT: $HasGit"
    Write-Output "SPECIFY_CHANGE_ID environment variable set to: $BranchName"
}

