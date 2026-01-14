#!/usr/bin/env pwsh
<#
.SYNOPSIS
Synchronize the Copilot instructions file with current governance and project state.

 .DESCRIPTION
The update-agent-context.ps1 script extracts governance principles, tech stack,
code conventions, and architecture patterns from your constitution and project files,
then updates the GitHub Copilot instructions file to ensure Copilot has current project
context for code generation and assistance.

The script:
- Extracts governance principles from specs/memory/constitution.md
- Extracts tech stack from specs/project.md (frontend/backend)
- Extracts code conventions and architecture patterns
- Lists active changes in specs/changes/
- Generates the standardized Copilot instructions file
- Creates parent directories if they don't exist

Supported agent types:
- copilot: .github/copilot-instructions.md

Operates from hybrid folder by default, using specs/ as the authoritative location.

.PARAMETER AgentType
Specify which agent context to update. Valid values: copilot, all. If omitted or set to empty string, updates
the Copilot instructions file.

 .EXAMPLE
./update-agent-context.ps1

Updates the Copilot instructions file with current governance and project state.

 .EXAMPLE
./update-agent-context.ps1 -AgentType copilot

Updates only the GitHub Copilot instructions file at .github/copilot-instructions.md.

 .EXAMPLE
cd hybrid
./specs/scripts/update-agent-context.ps1 -AgentType all

Run from the hybrid folder (recommended) and explicitly update the Copilot instructions.

 .EXAMPLE
./update-agent-context.ps1 -AgentType all

Explicitly update the Copilot instructions.

.NOTES
Exit Codes:
    0 - Success (Copilot instructions updated)
  1 - Failure (validation failed or update error)

Prerequisites:
  - specs/memory/constitution.md (required for governance principles)
  - specs/project.md (recommended for tech stack and conventions)
  - common.ps1 in same directory (for helper functions)

Architecture References:
  - SpecKit Architecture: docs/speckit/ARCHITECTURE_OVERVIEW.md
  - File-Based State: docs/speckit/architecture/ADR-0002-file-based-state.md
  - Constitution Agent: docs/speckit/agents/speckit.constitution.agent.md

Governance Context:
  This script uses governance-based context extraction (not plan.md extraction).
  The governance extraction logic should eventually be refactored into common.ps1
  for reuse across scripts (see Issue #9).

Validation:
  - Warns if constitution.md is missing
  - Continues with warning if project.md is missing
  - Creates parent directories automatically
    - Reports success/failure for Copilot instructions update

Issues:
  - Issue #6: Help system implementation (COMPLETE)
  - Issue #9: Governance extraction refactoring (DEFERRED)

.LINK
https://github.com/rephlex/speckit

.LINK
docs/speckit/ARCHITECTURE_OVERVIEW.md
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet('copilot','all','')]
    [string]$AgentType = '',

    [Parameter(HelpMessage="Display help message")]
    [switch]$Help,

    [Parameter(HelpMessage="Return machine-readable JSON output")]
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    @"

NAME
    update-agent-context.ps1

SYNOPSIS
    Synchronize the Copilot instructions file with current governance and project state.

DESCRIPTION
    The update-agent-context.ps1 script extracts governance principles, tech stack,
    code conventions, and architecture patterns from your constitution and project files,
    then updates the GitHub Copilot instructions file to ensure Copilot has current project
    context for code generation and assistance.

    Supported agent types:
    - copilot: .github/copilot-instructions.md

PARAMETERS
    -AgentType <string>
        Specify which agent context to update.
        Valid values: copilot, all
        If omitted or empty string, updates the Copilot instructions file.

    -Help
        Display this help message.

EXAMPLES
    ./update-agent-context.ps1
        Updates the Copilot instructions file with current governance and project state.

    ./update-agent-context.ps1 -AgentType copilot
        Updates only the GitHub Copilot instructions file.

NOTES
    File: update-agent-context.ps1
    Author: SpecKit Consolidated
    Requires: PowerShell 7+
    Prerequisites: specs/memory/constitution.md (required), specs/project.md (recommended)

"@
    exit 0
}

# Import common helpers
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")

# Acquire environment paths
$EnvData = Get-FeaturePathsEnv
$RepoRoot = $EnvData.REPO_ROOT

# Use current working directory as repo root if specs/ folder exists (same logic as setup-document.ps1)
if (Test-Path (Join-Path (Get-Location) "specs")) {
    $RepoRoot = (Get-Location).Path
}

$SpecsDir = Join-Path $RepoRoot "specs"
$ConstitutionFile = Join-Path $SpecsDir "memory" "constitution.md"
$ProjectFile = Join-Path $SpecsDir "project.md"

# Agent file paths (Copilot-only scope)
$AgentFiles = @{
    'copilot'  = Join-Path $RepoRoot '.github' 'copilot-instructions.md'
}

# Governance data (populated by Get-GovernanceContext)
$Script:GovernancePrinciples = @()
$Script:TechStackFrontend = @()
$Script:TechStackBackend = @()
$Script:TechStackNotes = @()
$Script:FeatureTechConstraints = @()
$Script:CodeConventions = @()
$Script:ArchitecturePatterns = @()

function Get-BulletedItems {
    param(
        [Parameter(Mandatory)]
        [string]$MarkdownSection
    )

    $Items = [regex]::Matches($MarkdownSection, '(?m)^\s*[-*]\s+(.+?)\s*$') |
        ForEach-Object { $_.Groups[1].Value.Trim() }

    # Strip common markdown formatting noise
    $Items = $Items | ForEach-Object {
        ($_ -replace '^\*\*(.+?)\*\*$', '$1').Trim()
    }

    return ($Items | Where-Object { $_ } | Select-Object -Unique)
}

function Add-TechItems {
    param(
        [Parameter(Mandatory)]$Target,
        [Parameter(Mandatory)][string[]]$Items
    )
    foreach ($I in $Items) {
        if ($I -and ($Target -notcontains $I)) { $Target += $I }
    }
    return $Target
}

function Write-SpecKitInfo {
    param([string]$Message)
    Write-Host "[speckit] $Message" -ForegroundColor Cyan
}

function Write-SpecKitSuccess {
    param([string]$Message)
    Write-Host "[speckit] $Message" -ForegroundColor Green
}

function Write-SpecKitWarning {
    param([string]$Message)
    Write-Host "[speckit] $Message" -ForegroundColor Yellow
}

function Write-SpecKitError {
    param([string]$Message)
    Write-Host "[speckit] $Message" -ForegroundColor Red
}

function Test-SpecKitEnvironment {
    if (-not (Test-Path $ConstitutionFile)) {
        Write-SpecKitError "Constitution file not found: ${constitutionFile}"
        Write-SpecKitInfo "Run speckit.constitution agent or create specs/memory/constitution.md"
        return $False
    }
    if (-not (Test-Path $ProjectFile)) {
        Write-SpecKitWarning "Project file not found: ${projectFile}"
        Write-SpecKitInfo "Copilot instructions will use constitution only"
    }
    return $True
}

function Get-GovernanceContext {
    Write-SpecKitInfo "Extracting governance context..."


        # Prefer consolidated extraction from common.ps1 (cached)
        try {
            $Gov = Get-GovernanceData -ConstitutionPath $ConstitutionFile -ProjectPath $ProjectFile

            $Script:GovernancePrinciples = @($Gov.Principles)
            $Script:CodeConventions = @($Gov.CodeConventions)
            $Script:ArchitecturePatterns = @($Gov.ArchitecturePatterns)

            if ($Gov.TechStack) {
                $Script:TechStackFrontend = @($Gov.TechStack.frontend)
                $Script:TechStackBackend  = @($Gov.TechStack.backend)
            }

            if (($Script:TechStackFrontend.Count + $Script:TechStackBackend.Count) -eq 0) {
                $Script:TechStackNotes = @('No technology stack bullets were detected in specs/project.md under "## Tech Stack". Context will omit stack items until project.md includes bullet lists.')
            }
        } catch {
            Write-SpecKitWarning "Failed to read consolidated governance data: $($_.Exception.Message)"
            $Script:TechStackNotes = @('Governance/tech stack extraction failed; generated context contains governance principles only.')
        }

        # Feature-specific tech constraints (best-effort) from active change spec/plan
        try {
            $ChangeId = Get-CurrentChangeId
            if ($ChangeId) {
                $FeatureDir = Get-FeatureDir -FeatureId $ChangeId
                if ($FeatureDir -and (Test-Path $FeatureDir)) {
                    foreach ($Rel in @('spec.md','plan.md')) {
                        $P = Join-Path $FeatureDir $Rel
                        if (-not (Test-Path $P)) { continue }
                        $Content = Get-Content $P -Raw

                        # Match sections commonly used for constraints (kept permissive across templates)
                        foreach ($Header in @('Technical Constraints','Tech Constraints','Constraints','Technology Constraints')) {
                            $Pattern = '(?s)##\s+' + [regex]::Escape($Header) + '\s*\n(?<sec>.+?)(?=\n##\s|\z)'
                            if ($Content -match $Pattern) {
                                $Items = Get-BulletedItems -MarkdownSection $Matches['sec']
                                if ($Items.Count -gt 0) {
                                    $Script:FeatureTechConstraints = @($Script:FeatureTechConstraints + $Items | Select-Object -Unique)
                                }
                            }
                        }

                        # Also catch inline "Tech Stack" headings in change artifacts (rare but useful)
                        if ($Content -match '(?s)##\s+Tech Stack\s*\n(?<sec>.+?)(?=\n##\s|\z)') {
                            $Items = Get-BulletedItems -MarkdownSection $Matches['sec']
                            if ($Items.Count -gt 0) {
                                $Script:FeatureTechConstraints = @($Script:FeatureTechConstraints + $Items | Select-Object -Unique)
                            }
                        }
                    }
                }
            }
        } catch {
            # Non-fatal; feature context may not exist yet
        }

        # If consolidated mode didn't populate principles (e.g., missing constitution), preserve prior behavior warning.
        if ($Script:GovernancePrinciples.Count -eq 0 -and (Test-Path $ConstitutionFile)) {
            $ConstitutionContent = Get-Content $ConstitutionFile -Raw
            if ($ConstitutionContent -match '(?s)## Core Principles\s*\n(.+?)(?=\n## |\z)') {
                $PrinciplesSection = $Matches[1]
                $Script:GovernancePrinciples = [regex]::Matches($PrinciplesSection, '### ([IVX]+\. [^\n]+)\s*\n+([^#]+?)(?=\n###|\z)') | ForEach-Object {
                    @{
                        title = $_.Groups[1].Value.Trim()
                        summary = ($_.Groups[2].Value -split '\n' | Where-Object { $_ -match '\S' } | Select-Object -First 1) -join ' '
                    }
                }
            }
        }

        Write-SpecKitSuccess "Extracted governance context:"
        Write-Host "  - Governance Principles: $($GovernancePrinciples.Count)"
        Write-Host "  - Frontend Technologies: $($TechStackFrontend.Count)"
        Write-Host "  - Backend Technologies: $($TechStackBackend.Count)"
        Write-Host "  - Feature Tech Constraints: $($FeatureTechConstraints.Count)"
        Write-Host "  - Code Conventions: $($CodeConventions.Count)"
        Write-Host "  - Architecture Patterns: $($ArchitecturePatterns.Count)"
}

function Set-MarkedSection {
        <#
        .SYNOPSIS
            Replaces only the content within a BEGIN/END marker pair.
        .DESCRIPTION
            Preserves any manual edits outside the auto-generated region.
        #>
        param(
            [Parameter(Mandatory)][string]$ExistingContent,
            [Parameter(Mandatory)][string]$NewAutoContent,
            [string]$BeginMarker = '<!-- BEGIN SPECKIT AUTO -->',
            [string]$EndMarker = '<!-- END SPECKIT AUTO -->'
        )

        $EscapedBegin = [regex]::Escape($BeginMarker)
        $EscapedEnd = [regex]::Escape($EndMarker)
        $Pattern = "(?s)${escapedBegin}.*?${escapedEnd}"
        $Replacement = "$BeginMarker`n$NewAutoContent`n$EndMarker"

        if ($ExistingContent -match $Pattern) {
            return [regex]::Replace($ExistingContent, $Pattern, $Replacement, 1)
        }

        # If markers do not exist, append a separated auto block.
        $Suffix = if ($ExistingContent -and -not $ExistingContent.EndsWith("`n")) { "`n" } else { '' }
        return ($ExistingContent + $Suffix + "`n$Replacement`n")
    }

    function Format-TechStackSection {
        param(
            [string[]]$Frontend,
            [string[]]$Backend,
            [string[]]$Notes,
            [string[]]$FeatureConstraints
        )

        $Sb = New-Object System.Text.StringBuilder
        [void]$Sb.AppendLine('## Technology Stack')
        [void]$Sb.AppendLine('')

        if ($Frontend -and $Frontend.Count -gt 0) {
            [void]$Sb.AppendLine('### Frontend')
            foreach ($I in $Frontend) { [void]$Sb.AppendLine("- $I") }
            [void]$Sb.AppendLine('')
        }

        if ($Backend -and $Backend.Count -gt 0) {
            [void]$Sb.AppendLine('### Backend')
            foreach ($I in $Backend) { [void]$Sb.AppendLine("- $I") }
            [void]$Sb.AppendLine('')
        }

        if ((-not $Frontend -or $Frontend.Count -eq 0) -and (-not $Backend -or $Backend.Count -eq 0) -and (-not $FeatureConstraints -or $FeatureConstraints.Count -eq 0)) {
            [void]$Sb.AppendLine('Not specified (see specs/project.md)')
            if ($Notes -and $Notes.Count -gt 0) {
                [void]$Sb.AppendLine('')
                [void]$Sb.AppendLine('### Notes')
                foreach ($N in ($Notes | Where-Object { $_ })) {
                    [void]$Sb.AppendLine("- $N")
                }
            }
        }

        if ($FeatureConstraints -and $FeatureConstraints.Count -gt 0) {
            if ($Sb.ToString() -notmatch '\n\n$') { [void]$Sb.AppendLine('') }
            [void]$Sb.AppendLine('### Feature-Specific Tech Constraints')
            foreach ($C in $FeatureConstraints) { [void]$Sb.AppendLine("- $C") }
        }

        return $Sb.ToString().TrimEnd()
    }

function Get-TechStackFromActiveFeatures {
    <#
    .SYNOPSIS
        Fallback tech stack extraction from active feature specs/plans.
    .DESCRIPTION
        When project.md is incomplete, we scan active changes under
        specs/changes/ for any explicit tech stack sections or technical
        context tables and use those.
    #>

    $ChangesDir = Join-Path $SpecsDir 'changes'
    if (-not (Test-Path $ChangesDir)) { return }

    $Active = Get-ChildItem -Path $ChangesDir -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'archive' }

    foreach ($Change in $Active) {
        $SpecPath = Join-Path $Change.FullName 'spec.md'
        $PlanPath = Join-Path $Change.FullName 'plan.md'

        foreach ($Path in @($SpecPath, $PlanPath)) {
            if (-not (Test-Path $Path)) { continue }
            $Content = Get-Content -LiteralPath $Path -Raw

            # Use robust extractor from common.ps1
            $Tech = Extract-TechStack -ProjectContent $Content
            $HasItems = $False

            if ($Tech.frontend.Count -gt 0) {
                # Add to feature constraints for context prominence (Issue #21)
                $Script:FeatureTechConstraints = Add-TechItems -Target $Script:FeatureTechConstraints -Items $Tech.frontend
                $HasItems = $True
            }
            if ($Tech.backend.Count -gt 0) {
                $Script:FeatureTechConstraints = Add-TechItems -Target $Script:FeatureTechConstraints -Items $Tech.backend
                $HasItems = $True
            }

            # Clear "not specified" notes if we found actual tech in features
            if ($HasItems) { $Script:TechStackNotes = @() }

            # Also specifically extract Technical Constraints / Constraints for Feature Tech Constraints
            foreach ($Header in @('Technical Context', 'Technical Constraints', 'Tech Constraints', 'Constraints', 'Technology Constraints')) {
                $Pattern = '(?im)^##\s+' + [regex]::Escape($Header) + '\s*[\r\n]+(?<sec>(?s).+?)(?=\r?\n##\s|\z)'
                if ($Content -match $Pattern) {
                    $Items = Get-BulletedItems -MarkdownSection $Matches['sec']
                    if ($Items.Count -gt 0) {
                        $Script:FeatureTechConstraints = Add-TechItems -Target $Script:FeatureTechConstraints -Items $Items
                        $Script:TechStackNotes = @()
                    }
                }
            }
        }
    }
}

function Get-AgentContextContent {
    param([string]$AgentName)

    $Timestamp = Get-StandardTimestamp
    $ProjectName = Split-Path $RepoRoot -Leaf

    $Content = @"
# $AgentName Context for $ProjectName

**Last Updated**: $Timestamp

## Project Overview

This project follows SpecKit Consolidated governance with spec-first development and file-based truth.

## Governance Principles

"@

    if ($GovernancePrinciples.Count -gt 0) {
        foreach ($Principle in $GovernancePrinciples) {
            $Content += "`n### $($Principle.title)`n`n$($Principle.summary)`n"
        }
    } else {
        $Content += "`nSee specs/memory/constitution.md for complete governance principles.`n"
    }

    $Content += "`n`n" + (Format-TechStackSection -Frontend $TechStackFrontend -Backend $TechStackBackend -Notes $TechStackNotes -FeatureConstraints $FeatureTechConstraints) + "`n"

    $Content += @"


## Code Conventions
"@

    if ($CodeConventions.Count -gt 0) {
        foreach ($Convention in $CodeConventions) {
            $Content += "`n- $Convention"
        }
    } else {
        $Content += "`n- See specs/project.md for code style conventions"
    }

    $Content += @"


## Architecture Patterns
"@

    if ($ArchitecturePatterns.Count -gt 0) {
        foreach ($Pattern in $ArchitecturePatterns) {
            $Content += "`n- $Pattern"
        }
    } else {
        $Content += "`n- See specs/project.md for architecture patterns"
    }

    # List active changes
    $ChangesDir = Join-Path $SpecsDir "changes"
    $ActiveChanges = Get-ChildItem -Path $ChangesDir -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "archive" }

    $Content += @"


## Active Changes
"@

    if ($ActiveChanges.Count -gt 0) {
        foreach ($Change in $ActiveChanges) {
            $Content += "`n- $($Change.Name)"
        }
    } else {
        $Content += "`n- No active changes"
    }

    $Content += @"


## SpecKit Workflow

All features follow the 11-phase SpecKit workflow:

1. **document** - Generate workflow guide
2. **constitution** - Verify governance
3. **specify** - Create specification
4. **clarify** - Resolve ambiguities
5. **plan** - Technical implementation plan
6. **tasks** - Task breakdown
7. **checklist** - Acceptance criteria
8. **taskstoissues** - Convert to GitHub issues
9. **analyze** - Validate consistency
10. **implement** - Execute implementation
11. **archive** - Archive and promote to truth

## References

- Constitution: specs/memory/constitution.md
- Project Context: specs/project.md
- Changes: specs/changes/
- SpecKit Agents: .github/agents/
"@

    return $Content
}

function Update-AgentFile {
    param(
        [string]$FilePath,
        [string]$AgentName
    )

    Write-SpecKitInfo "Updating $AgentName context: ${FilePath}"

    # Ensure parent directory exists
    $ParentDir = Split-Path $FilePath -Parent
    if (-not (Test-Path $ParentDir)) {
        New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
    }

    # Generate content (auto-managed block)
    $Content = Get-AgentContextContent -AgentName $AgentName

    # Preserve manual edits using markers
    $Begin = '<!-- BEGIN SPECKIT AUTO -->'
    $End = '<!-- END SPECKIT AUTO -->'

    $Wrapped = "$Begin`n$Content`n$End`n"

    if (Test-Path $FilePath) {
        $Existing = Get-Content -LiteralPath $FilePath -Raw

        if ($Existing -match [regex]::Escape($Begin) + '(?s).*' + [regex]::Escape($End)) {
            $Updated = [regex]::Replace(
                $Existing,
                [regex]::Escape($Begin) + '(?s).*' + [regex]::Escape($End),
                ($Wrapped.TrimEnd() -replace '\\', '\\')
            )
            Set-Content -LiteralPath $FilePath -Value $Updated -Encoding UTF8
        }
        else {
            # No markers present yet: replace entire file with a single managed block.
            # This avoids duplicated context sections from earlier generations.
            Set-Content -LiteralPath $FilePath -Value $Wrapped -Encoding UTF8
        }
    }
    else {
        Set-Content -LiteralPath $FilePath -Value $Wrapped -Encoding UTF8
    }

    Write-SpecKitSuccess "Updated $AgentName context file"
}

function Update-AllAgents {
    $Updated = 0

    foreach ($Agent in $AgentFiles.Keys) {
        $FilePath = $AgentFiles[$Agent]
        $AgentName = $Agent.Substring(0,1).ToUpper() + $Agent.Substring(1)

        try {
            Update-AgentFile -FilePath $FilePath -AgentName $AgentName
            $Updated++
        }
        catch {
            Write-SpecKitError "Failed to update ${agentName} : $_"
        }
    }

    return $Updated
}

function Update-SpecificAgent {
    param([string]$Type)

    if (-not $AgentFiles.ContainsKey($Type)) {
        Write-SpecKitError "Unknown agent type: ${Type}"
        Write-SpecKitInfo "Valid types: $($AgentFiles.Keys -join ', ')"
        return $False
    }

    $FilePath = $AgentFiles[$Type]
    $AgentName = $Type.Substring(0,1).ToUpper() + $Type.Substring(1)

    try {
        Update-AgentFile -FilePath $FilePath -AgentName $AgentName
        return $True
    }
    catch {
        Write-SpecKitError "Failed to update ${agentName} : $_"
        return $False
    }
}

function Invoke-Main {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  SpecKit Agent Context Update (Copilot Only)" -ForegroundColor White
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-SpecKitInfo "Repository: ${repoRoot}"
    Write-Host ""

    # Validate environment
    if (-not (Test-SpecKitEnvironment)) {
        exit 1
    }

    # Extract governance context
    Get-GovernanceContext

    # Augment: scan active features for additional tech stack/constraints (Issue #21)
    Write-SpecKitInfo "Augmenting tech stack from active features..."
    Get-TechStackFromActiveFeatures
    Write-Host "  - Frontend Technologies (total): $($TechStackFrontend.Count)"
    Write-Host "  - Backend Technologies (total): $($TechStackBackend.Count)"
    Write-Host "  - Feature Tech Constraints (total): $($FeatureTechConstraints.Count)"
    Write-Host ""

    # Update agent files (Copilot-only)
    if ($AgentType -eq 'all' -or $AgentType -eq '') {
        Write-SpecKitInfo "Updating Copilot instructions file..."
        $Count = Update-AllAgents
        Write-Host ""
        Write-SpecKitSuccess "Updated $Count Copilot instructions file(s)"
    }
    else {
        Write-SpecKitInfo "Updating specific agent: ${AgentType}"
        if (Update-SpecificAgent -Type $AgentType) {
            Write-Host ""
            Write-SpecKitSuccess "Copilot instructions update complete"
        }
        else {
            Write-Host ""
            Write-SpecKitError "Copilot instructions update failed"
            exit 1
        }
    }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-SpecKitSuccess "Copilot instructions sync complete"
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

Invoke-Main

