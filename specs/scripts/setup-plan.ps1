#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup implementation plan for SpecKit workflow.

.DESCRIPTION
    Prepares the planning phase of SpecKit by:
    - Validating that spec.md exists (prerequisite from specify phase)
    - Creating plan.md from plan-template.md if it doesn't exist
    - Extracting CHANGE_ID from directory path or git branch
    - Returning all necessary paths for the plan agent

    This script is used by speckit.plan agent to initialize the planning workspace
    before the agent generates the implementation plan content.

.PARAMETER Json
    Output results in JSON format (single line, compressed).
    Useful for automation and agent consumption.

.PARAMETER Help
    Display this help message and exit.

.PARAMETER FeatureId
    Optional. Override the detected change id / feature id for testing or automation.

.PARAMETER Force
    Optional switch. When specified, existing files will be overwritten.

.PARAMETER WhatIf
    Optional switch. Dry-run mode: show planned changes without making any filesystem changes.

.EXAMPLE
    .\setup-plan.ps1

    Performs standard plan setup and displays results in human-readable format.
    Shows repository root, branch name, spec file, and plan file locations.

.EXAMPLE
    .\setup-plan.ps1 -Json

    Returns plan setup information as JSON for agent consumption:
    {"REPO_ROOT":"C:\\repo","BRANCH":"feat/new-feature","CHANGE_ID":"feat-new-feature",...}

.NOTES
    File Name      : setup-plan.ps1
    Prerequisite   : common.ps1 must be in the same directory
    Used By        : speckit.plan agent

    Exit Codes:
    - 0: Success (plan.md ready for editing)
    - 1: Failure (missing feature directory, spec.md, or template)

    Required Files:
    - specs/changes/<branch-name>/spec.md (from specify phase)
    - specs/templates/plan-template.md (used to create plan.md if needed)

    Changelog:
    - 2026-01-13 B.1: Multi-template copy (plan, research, data-model, quickstart), create contracts directory, add -WhatIf & -Force, and rollback on error.

    This script validates prerequisites per ADR-0002 (file-based state detection).

.LINK
    docs/speckit/ARCHITECTURE_OVERVIEW.md
    docs/speckit/architecture/ADR-0002-file-based-state.md
#>

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help,
    [string]$FeatureId,
    [switch]$Force,
    [switch]$WhatIf
)

# Display help if requested
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$ErrorActionPreference = 'Stop'

# Source common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")

# Allow overriding the target change id for testing/automation via -FeatureId
if ($PSBoundParameters.ContainsKey('FeatureId') -and $FeatureId) {
    # Get-CurrentChangeId checks SPECIFY_CHANGE_ID / SPECIFY_FEATURE - use SPECIFY_CHANGE_ID for clarity
    $Env:SPECIFY_CHANGE_ID = $FeatureId
}

$EnvData = Get-FeaturePathsEnv

$RepoRoot = $EnvData.REPO_ROOT
$CurrentBranch = $EnvData.CURRENT_BRANCH
$FeatureDir = $EnvData.FEATURE_DIR
$SpecFile = $EnvData.FEATURE_SPEC
$PlanFile = $EnvData.IMPL_PLAN

# Extract CHANGE_ID from directory name or branch name
$ChangeId = if ($FeatureDir -and (Test-Path $FeatureDir)) {
    (Split-Path -Leaf $FeatureDir)
} elseif ($CurrentBranch) {
    $CurrentBranch -replace '[/\\]', '-'
} else {
    "unknown"
}

# Validate prerequisites
if (-not (Test-Path $FeatureDir)) {
    $ErrorDetails = @{
        ERROR = "Feature directory not found"
        CONTEXT = "Plan setup requires an initialized feature directory"
        EXPECTED_PATH = $FeatureDir
        CURRENT_BRANCH = $CurrentBranch
        SUGGESTION = "Initialize feature: .\create-new-feature.ps1 or ensure you're on the correct branch"
    }
    if ($Json) {
        $ErrorDetails | ConvertTo-Json -Compress
    } else {
        Write-Error "Feature directory not found: $FeatureDir`nPlan setup requires an initialized feature directory.`nSuggestion: Run .\create-new-feature.ps1 to initialize the feature"
    }
    exit 1
}

if (-not (Test-Path $SpecFile)) {
    $ErrorDetails = @{
        ERROR = "Spec file not found"
        CONTEXT = "Plan setup requires spec.md from the specify phase"
        EXPECTED_PATH = $SpecFile
        CURRENT_BRANCH = $CurrentBranch
        CHANGE_ID = $ChangeId
        SUGGESTION = "Run /speckit.specify agent first to create spec.md"
        ALTERNATIVE = "Manually create spec.md in the feature directory"
    }
    if ($Json) {
        $ErrorDetails | ConvertTo-Json -Compress
    } else {
        Write-Error "Spec file not found: $SpecFile`nPlan setup requires spec.md from the specify phase.`nSuggestion: Run /speckit.specify agent first to create spec.md"
    }
    exit 1
}

# Multi-template initialization for Phase-1 artifacts (Workstream B.1)
# Use a concise template map (src = template filename in specs/templates, dest = filename under feature dir)
$Templates = @(
    @{ src = 'plan-template.md'; dest = 'plan.md' },
    @{ src = 'research-template.md'; dest = 'research.md' },
    @{ src = 'data-model-template.md'; dest = 'data-model.md' },
    @{ src = 'quickstart-template.md'; dest = 'quickstart.md' }
)

# Track artifacts created during this run so rollback only removes what we created
$CreatedFiles = @()
$CreatedDirs = @()
# Track backups of overwritten files (when -Force used) so we can restore on rollback
$OverwrittenBackups = @{}

try {
    # Ensure contracts directory exists (Issue #26 / Setup-Plan Artifact Gap)
    $ContractsDir = $EnvData.CONTRACTS_DIR
    if ($ContractsDir -and -not (Test-Path $ContractsDir)) {
        if ($WhatIf) {
            Write-Output "Would create directory: $ContractsDir"
        } else {
            New-Item -Path $ContractsDir -ItemType Directory -Force -ErrorAction Stop | Out-Null
            $CreatedDirs += $ContractsDir
            Write-Verbose "Created contracts directory: $ContractsDir"
        }
    } elseif ($WhatIf) {
        # Directory already exists but report the planned ensure step
        Write-Output "Would ensure directory exists: $ContractsDir"
    }

    foreach ($T in $Templates) {
        $SrcPath = Join-Path $EnvData.TEMPLATES_DIR $T.src
        $DestPath = Join-Path $FeatureDir $T.dest

        if ($WhatIf) {
            if (Test-Path $SrcPath) {
                Write-Output "Would copy '$SrcPath' -> '$DestPath'"
            } else {
                throw "Required template not found: $SrcPath"
            }
            continue
        }

        # Actual execution: fail fast if required template is missing
        if (-not (Test-Path $SrcPath)) {
            throw "Required template not found: $SrcPath"
        }

        if (Test-Path $DestPath) {
            if (-not $Force) {
                Write-Verbose "Preserving existing file (no -Force): $DestPath"
                continue
            } else {
                # Backup existing file so it can be restored if rollback is needed
                $BackupPath = Join-Path ([System.IO.Path]::GetTempPath()) ("setup-plan-backup-{0}.bak" -f ([Guid]::NewGuid().ToString()))
                Copy-Item $DestPath $BackupPath -Force -ErrorAction Stop
                $OverwrittenBackups[$DestPath] = $BackupPath
                Write-Verbose "Backed up existing file: $DestPath -> $BackupPath"
            }
        }

        Copy-Item $SrcPath $DestPath -Force -ErrorAction Stop
        if (-not $OverwrittenBackups.ContainsKey($DestPath)) {
            # Only mark as created if it did not exist before this run
            $CreatedFiles += $DestPath
        }
        Write-Verbose "Copied template: $SrcPath -> $DestPath"
    }

    # If this was a dry-run (WhatIf) we would have exited in the loop; continue normal completion
}
catch {
    # Rollback: remove only files/dirs created by this run, and restore overwritten files from backups
    if ($CreatedFiles.Count -gt 0 -or $CreatedDirs.Count -gt 0 -or $OverwrittenBackups.Count -gt 0) {
        Write-Warning "Rolling back: removing partially created artifacts..."

        foreach ($File in $CreatedFiles) {
            if (Test-Path $File) {
                Remove-Item $File -Force -ErrorAction SilentlyContinue
                Write-Verbose "Removed file: $File"
            }
        }

        foreach ($Dir in $CreatedDirs) {
            if (Test-Path $Dir) {
                Remove-Item $Dir -Recurse -Force -ErrorAction SilentlyContinue
                Write-Verbose "Removed directory: $Dir"
            }
        }

        # Restore backups for overwritten files
        foreach ($Kv in $OverwrittenBackups.GetEnumerator()) {
            $Dest = $Kv.Key
            $Backup = $Kv.Value
            if (Test-Path $Backup) {
                Copy-Item $Backup $Dest -Force -ErrorAction SilentlyContinue
                Remove-Item $Backup -Force -ErrorAction SilentlyContinue
                Write-Verbose "Restored overwritten file from backup: $Dest"
            }
        }
    }

    $ErrorDetails = @{
        ERROR = "Template initialization failed"
        CONTEXT = "Failed while copying templates to feature directory"
        DETAILS = $_.ToString()
        CREATED_FILES = $CreatedFiles
        CREATED_DIRS = $CreatedDirs
        RESTORED_BACKUPS = $OverwrittenBackups.Keys
        CURRENT_BRANCH = $CurrentBranch
        CHANGE_ID = $ChangeId
    }

    if ($Json) {
        $ErrorDetails | ConvertTo-Json -Compress
    } else {
        Write-Error "Template initialization failed: $($_.Exception.Message)`nRollback attempted (only artifacts created by this run were removed or restored)."
    }
    exit 1
}

$SpecsDir = Join-Path $RepoRoot "specs"
$Output = [PSCustomObject]@{
    REPO_ROOT       = $RepoRoot
    BRANCH          = $CurrentBranch
    CHANGE_ID       = $ChangeId
    FEATURE_DIR     = $FeatureDir
    FEATURE_SPEC    = $SpecFile
    IMPL_PLAN       = $PlanFile
    TASKS_FILE      = $EnvData.TASKS
    SPECS_DIR       = $SpecsDir
    CHANGES_DIR     = Join-Path $SpecsDir "changes"
    # Phase 0/1 artifact paths (Issue #26)
    RESEARCH_FILE   = $EnvData.RESEARCH
    DATA_MODEL_FILE = $EnvData.DATA_MODEL
    QUICKSTART_FILE = $EnvData.QUICKSTART
    CONTRACTS_DIR   = $EnvData.CONTRACTS_DIR
}

if ($Json) {
    $Output | ConvertTo-Json -Compress
} else {
    Write-Output "[speckit] Plan Setup Complete"
    Write-Output "============================="
    Write-Output "Branch: $CurrentBranch"
    Write-Output "Change ID: $ChangeId"
    Write-Output "Feature Directory: $FeatureDir"
    Write-Output "Spec File: $SpecFile"
    Write-Output "Plan File: $PlanFile"
}

