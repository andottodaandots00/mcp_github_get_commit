#!/usr/bin/env pwsh
# SpecKit Consolidated - common PowerShell functions
# Source: hybrid/scripts/common.ps1 (ported into specs/scripts)

# =============================================================================
# WORKSPACE ROOT DETECTION (T005, T006 - 001-openspec-integration)
# =============================================================================

# Cache for governance data extraction (K.2 / v4 Issue #1)
$Script:GovernanceDataCache = $Null
$Script:GovernanceDataCacheProjectPath = $Null

function Get-WorkspaceRoot {
    <#
    .SYNOPSIS
        Detects the workspace root by finding the SpecKit workspace directory
    .DESCRIPTION
        Uses multiple strategies to find workspace root:
        1. Script location: Go up 2 levels from specs/scripts/ and verify specs/memory/constitution.md exists
        2. Git root: Only if it contains specs/memory/constitution.md (valid SpecKit workspace)
        3. Walk-up search: From current directory looking for specs/memory/constitution.md
        This order ensures hybrid/ is detected when it's a subfolder of another git repo.

        SAFE FROM RECURSION (Issue #27):
        This function is a leaf-node for workspace detection and does not call any other functions
        that might source common.ps1 or call back into this function (like Test-HasGit).
    .OUTPUTS
        String path to workspace root, or $Null if not found
    #>

    # Helper to validate a SpecKit workspace root
    function Test-SpecKitRoot {
        param([string]$Path)
        if (-not $Path -or -not (Test-Path $Path)) { return $False }
        $Constitution = Join-Path $Path "specs" "memory" "constitution.md"
        return (Test-Path $Constitution)
    }

    # Strategy 1: Script location - go up 2 levels from specs/scripts/
    # This is the most reliable when running from within the workspace
    if ($PSScriptRoot) {
        try {
            $CandidateRoot = (Resolve-Path (Join-Path $PSScriptRoot ".." "..") -ErrorAction SilentlyContinue).Path
            if (Test-SpecKitRoot $CandidateRoot) {
                return $CandidateRoot
            }
        } catch {
            # Fall through to next strategy
        }
    }

    # Strategy 2: Git repository root - only if it's a valid SpecKit workspace
    # This handles the case where the SpecKit workspace IS the git root
    $SearchPath = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
    $Current = $SearchPath
    $MaxDepth = 10
    for ($I = 0; $I -lt $MaxDepth; $I++) {
        $GitDir = Join-Path $Current ".git"
        if (Test-Path $GitDir) {
            try {
                $GitRoot = git rev-parse --show-toplevel 2>$Null
                if ($LASTEXITCODE -eq 0 -and $GitRoot) {
                    $GitRootClean = $GitRoot.Trim()
                    # Only use git root if it's a valid SpecKit workspace
                    if (Test-SpecKitRoot $GitRootClean) {
                        return $GitRootClean
                    }
                }
            } catch {
                # Fall through to next strategy
            }
            break
        }
        $Parent = Split-Path $Current -Parent
        if (-not $Parent -or $Parent -eq $Current) { break }
        $Current = $Parent
    }

    # Strategy 3: Walk up from current location looking for specs/memory/constitution.md
    $SearchPath = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
    $Current = $SearchPath
    for ($I = 0; $I -lt $MaxDepth; $I++) {
        if (Test-SpecKitRoot $Current) {
            return $Current
        }
        $Parent = Split-Path $Current -Parent
        if (-not $Parent -or $Parent -eq $Current) {
            break
        }
        $Current = $Parent
    }

    # Strategy 4: Last resort - script location parent (original fallback)
    if ($PSScriptRoot) {
        $Fallback = (Resolve-Path (Join-Path $PSScriptRoot ".." "..") -ErrorAction SilentlyContinue).Path
        if ($Fallback) { return $Fallback }
    }

    return $Null
}

function Get-StandardDate {
    <#
    .SYNOPSIS
        Returns the current date in "yyyy-MM-dd" format.
    #>
    return Get-Date -Format "yyyy-MM-dd"
}

function Get-StandardTimestamp {
    <#
    .SYNOPSIS
        Returns the current timestamp in "yyyy-MM-dd HH:mm:ss" format.
    #>
    return Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

function Get-FeatureDir {
    <#
    .SYNOPSIS
        Gets the directory for a specific feature or the current feature
    .PARAMETER FeatureId
        Optional. The feature ID (e.g., "001-openspec-integration").
        If not provided, uses Get-CurrentChangeId to detect current feature.
    .OUTPUTS
        String path to feature directory, or $Null if not found
    #>
    param(
        [Parameter(Position=0)]
        [string]$FeatureId
    )

    $WorkspaceRoot = Get-WorkspaceRoot
    if (-not $WorkspaceRoot) {
        Write-Warning "[speckit] Could not determine workspace root"
        return $Null
    }

    if (-not $FeatureId) {
        $FeatureId = Get-CurrentChangeId
    }

    if (-not $FeatureId) {
        Write-Warning "[speckit] No feature ID provided and could not detect current feature"
        return $Null
    }

    # Check in specs/changes/{feature}/ first (primary location for active features)
    $ChangesFeatureDir = Join-Path $WorkspaceRoot "specs" "changes" $FeatureId
    if (Test-Path $ChangesFeatureDir) {
        return $ChangesFeatureDir
    }

    # Check in specs/{feature}/ (legacy or alternative location)
    $SpecsFeatureDir = Join-Path $WorkspaceRoot "specs" $FeatureId
    if (Test-Path $SpecsFeatureDir) {
        return $SpecsFeatureDir
    }

    # Return expected path even if doesn't exist yet (for creation)
    return $ChangesFeatureDir
}

function Get-RepoRoot {
    # Delegate to Get-WorkspaceRoot which has proper SpecKit detection
    return Get-WorkspaceRoot
}

function Get-RepositoryRoot {
    <#
    .SYNOPSIS
        Canonical repository root accessor for hybrid SpecKit.
    .DESCRIPTION
        Wrapper around Get-WorkspaceRoot to provide a single, clear API name.
        Existing callers of Get-RepoRoot/Get-WorkspaceRoot remain supported.
    #>
    return Get-WorkspaceRoot
}

function Get-CurrentChangeId {
    # Preferred
    if ($Env:SPECIFY_CHANGE_ID) {
        return $Env:SPECIFY_CHANGE_ID
    }

    # Legacy support (deprecated)
    if ($Env:SPECIFY_FEATURE) {
        Write-Warning "[speckit] SPECIFY_FEATURE is deprecated. Use SPECIFY_CHANGE_ID instead."
        return $Env:SPECIFY_FEATURE
    }

    # Then check git if available
    try {
        $Result = git rev-parse --abbrev-ref HEAD 2>$Null
        if ($LASTEXITCODE -eq 0 -and $Result -match '^(add|update|remove|fix|feat|refactor|[\d]{3})[-/]') {
            return $Result
        }
    }
    catch {
        # Git command failed
    }

    # For non-git repos, try to find the latest change directory
    $RepoRoot = Get-RepositoryRoot
    $ChangesDir = Join-Path $RepoRoot "specs\changes"

    if (Test-Path $ChangesDir) {
        $LatestChange = ""
        $Highest = 0

        Get-ChildItem -Path $ChangesDir -Directory | Where-Object { $_.Name -ne 'archive' } | ForEach-Object {
            if ($_.Name -match '^(\d+)-') {
                $Num = [int]$Matches[1]
                if ($Num -gt $Highest) {
                    $Highest = $Num
                    $LatestChange = $_.Name
                }
            }
        }

        if ($LatestChange) {
            return $LatestChange
        }
    }

    return $Null
}

function Test-HasGit {
    <#
    .SYNOPSIS
        Checks if the current directory is within a Git repository (T007 - graceful Git detection)
    .DESCRIPTION
        First checks if .git directory exists, then validates with git command.
        Returns $False gracefully without errors if Git is unavailable.
    .OUTPUTS
        Boolean - $True if in Git repo, $False otherwise
    #>

    # Validate with git command (worktree/submodule safe)
    try {
        $Null = git rev-parse --git-dir 2>$Null
        if ($LASTEXITCODE -ne 0) { return $False }
        $Null = git rev-parse --show-toplevel 2>$Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        Write-Verbose "[speckit] Git command not available"
        return $False
    }
}

function Get-SpecKitPaths {
    <#
    .SYNOPSIS
        Returns commonly used SpecKit paths for the current workspace.
    .OUTPUTS
        Hashtable of absolute paths.
    #>
    $Root = Get-WorkspaceRoot
    if (-not $Root) { return @{} }

    $SpecsDir = Join-Path $Root 'specs'
    $MemoryDir = Join-Path $SpecsDir 'memory'
    $TemplatesDir = Join-Path $SpecsDir 'templates'

    return @{
        REPO_ROOT = $Root
        SPECS_DIR = $SpecsDir
        MEMORY_DIR = $MemoryDir
        TEMPLATES_DIR = $TemplatesDir
        WORKFLOW_PATH = (Join-Path $SpecsDir 'workflows')
        PROPOSAL_PATH = (Join-Path $SpecsDir 'proposals')
        CONSTITUTION_PATH = (Join-Path $MemoryDir 'constitution.md')
        PROJECT_PATH = (Join-Path $SpecsDir 'project.md')
    }
}

function Get-CurrentBranch {
    try {
        $Branch = git rev-parse --abbrev-ref HEAD 2>$Null
        if ($LASTEXITCODE -eq 0 -and $Branch) {
            return $Branch.Trim()
        }
    }
    catch {
        # Ignore and fall back
    }

    return "none"
}

function Test-ChangeId {
    param(
        [string]$ChangeId,
        [bool]$HasGit = $True
    )

    if (-not $HasGit) {
        Write-Warning "[speckit] Warning: Git repository not detected; skipped branch validation"
        return $True
    }

    if ($ChangeId -notmatch '^(add|update|remove|fix|feat|refactor|[0-9]{3})[-/]') {
        Write-Output "ERROR: Not on a valid change branch. Current: $ChangeId"
        Write-Output "Use: add-feature-name, feat/feature-name, 001-feature-name, etc."
        return $False
    }
    return $True
}

function Test-FeatureBranch {
    param([string]$Branch, [bool]$HasGit = $True)
    return Test-ChangeId -ChangeId $Branch -HasGit $HasGit
}

function Get-ChangeDir {
    param([string]$RepoRoot, [string]$ChangeId)

    # Check in specs/changes/{id}/ first (primary location for active features)
    $ChangesFeatureDir = Join-Path $RepoRoot "specs" "changes" $ChangeId
    if (Test-Path $ChangesFeatureDir) {
        return $ChangesFeatureDir
    }

    # Check in specs/{id}/ (legacy or alternate location)
    $SpecsFeatureDir = Join-Path $RepoRoot "specs" $ChangeId
    if (Test-Path $SpecsFeatureDir) {
        return $SpecsFeatureDir
    }

    # Default to specs/changes/ for creation/compatibility
    return Join-Path $RepoRoot "specs" "changes" $ChangeId
}

function Get-FeaturePathsEnv {
    $RepoRoot = Get-RepositoryRoot
    $ChangeId = Get-CurrentChangeId
    $HasGit = Test-HasGit
    $ChangeDir = if ($ChangeId) { Get-ChangeDir -RepoRoot $RepoRoot -ChangeId $ChangeId } else { $Null }

    $SpecsDir = Join-Path $RepoRoot "specs"
    $ChangesDir = Join-Path $SpecsDir "changes"
    $ArchiveDir = Join-Path $ChangesDir "archive"
    $MemoryDir = Join-Path $SpecsDir "memory"
    $TemplatesDir = Join-Path $SpecsDir "templates"

    [PSCustomObject]@{
        REPO_ROOT      = $RepoRoot
        CHANGE_ID      = $ChangeId
        CURRENT_BRANCH = $ChangeId
        HAS_GIT        = $HasGit

        SPECS_DIR      = $SpecsDir
        CHANGES_DIR    = $ChangesDir
        ARCHIVE_DIR    = $ArchiveDir
        TEMPLATES_DIR  = $TemplatesDir

        # Governance file paths (Issue #2 fix)
        CONSTITUTION   = Join-Path $MemoryDir "constitution.md"
        PROJECT        = Join-Path $SpecsDir "project.md"

        FEATURE_DIR    = $ChangeDir
        FEATURE_SPEC   = if ($ChangeDir) { Join-Path $ChangeDir 'spec.md' } else { $Null }
        IMPL_PLAN      = if ($ChangeDir) { Join-Path $ChangeDir 'plan.md' } else { $Null }
        TASKS          = if ($ChangeDir) { Join-Path $ChangeDir 'tasks.md' } else { $Null }
        RESEARCH       = if ($ChangeDir) { Join-Path $ChangeDir 'research.md' } else { $Null }
        DATA_MODEL     = if ($ChangeDir) { Join-Path $ChangeDir 'data-model.md' } else { $Null }
        QUICKSTART     = if ($ChangeDir) { Join-Path $ChangeDir 'quickstart.md' } else { $Null }
        CONTRACTS_DIR  = if ($ChangeDir) { Join-Path $ChangeDir 'contracts' } else { $Null }
        CHECKLISTS_DIR = if ($ChangeDir) { Join-Path $ChangeDir 'checklists' } else { $Null }
        CHECKLIST      = if ($ChangeDir) { Join-Path $ChangeDir 'checklist.md' } else { $Null }
        DELTA_SPECS    = if ($ChangeDir) { Join-Path $ChangeDir 'specs' } else { $Null }

        # Change-specific workflow paths (Issue #2 fix)
        WORKFLOW       = if ($ChangeDir) { Join-Path $ChangeDir 'workflow.md' } else { $Null }
        PROPOSAL       = if ($ChangeDir) { Join-Path $ChangeDir 'proposal.md' } else { $Null }
    }
}

# =============================================================================
# GOVERNANCE EXTRACTION FUNCTIONS (Issue #9 - Code Deduplication)
# =============================================================================
# These functions extract governance context from constitution.md and project.md
# Previously duplicated in setup-document.ps1 and update-agent-context.ps1
# =============================================================================

function Get-Principles {
    <#
    .SYNOPSIS
        Extracts Core Principles from constitution.md
    .DESCRIPTION
        Parses the Core Principles section and returns an array of principle objects
        with title and summary properties.
    .PARAMETER ConstitutionContent
        Raw content of constitution.md file
    .OUTPUTS
        Array of hashtables with 'title' and 'summary' keys
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$ConstitutionContent
    )

    $Principles = @()

    if ($ConstitutionContent -match '(?s)## Core Principles\s*\n(.+?)(?=\n## |\z)') {
        $PrinciplesSection = $Matches[1]
        $Principles = [regex]::Matches($PrinciplesSection, '### ([IVX]+\. [^\n]+)\s*\n+([^#]+?)(?=\n###|\z)') | ForEach-Object {
            @{
                title = $_.Groups[1].Value.Trim()
                summary = ($_.Groups[2].Value -split '\n' | Where-Object { $_ -match '\S' } | Select-Object -First 2) -join ' '
            }
        }
    }

    return $Principles
}

function Get-TechStack {
    <#
    .SYNOPSIS
        Extracts tech stack information from project.md
    .DESCRIPTION
        Parses Frontend and Backend sections and returns a hashtable
        with frontend and backend arrays.
    .PARAMETER ProjectContent
        Raw content of project.md file
    .OUTPUTS
        Hashtable with 'frontend' and 'backend' arrays
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$ProjectContent
    )

    $TechStack = @{ frontend = @(); backend = @() }

    function Get-BulletsFromSection {
        param([string]$SectionContent)

        if (-not $SectionContent) { return @() }

        $Items = [regex]::Matches($SectionContent, '(?m)^\s*[-*]\s+(.+?)\s*$') | ForEach-Object {
            $_.Groups[1].Value.Trim()
        }

        # Prefer bolded label ("- **Scripting**: PowerShell") but keep full line if no bold.
        $Items = $Items | ForEach-Object {
            $Line = $_
            if ($Line -match '^\*\*([^*]+)\*\*\s*:\s*(.+)$') {
                $Label = $Matches[1].Trim()
                $Value = $Matches[2].Trim()
                if ($Value) { return "${label}: $Value" }
                return $Label
            }
            ($Line -replace '^\*\*(.+?)\*\*$', '$1').Trim()
        }

        return ($Items | Where-Object { $_ } | Select-Object -Unique)
    }

    function Add-Unique {
        param([string[]]$Target, [string[]]$Items)
        $List = @($Target)
        foreach ($I in ($Items | Where-Object { $_ })) {
            if ($List -notcontains $I) { $List += $I }
        }
        return $List
    }

    # Match current hybrid/specs/project.md structure:
    # Supports: ## Tech Stack, ## Technology Stack, ## Development Tools
    $TopLevelPattern = '(?im)^##\s+(?:Tech Stack|Technology Stack|Development Tools)\s*[\r\n]+(?<section>(?s).+?)(?=\r?\n##\s|\z)'
    if ($ProjectContent -match $TopLevelPattern) {
        $TechSection = $Matches['section']

        # Explicit Frontend/Backend (future-proof)
        $SubPatterns = @{
            'frontend' = '(?im)^###\s+(?:Frontend|Frontend Tools)\s*[\r\n]+(?<sub>(?s).+?)(?=\r?\n###\s|\z)'
            'backend'  = '(?im)^###\s+(?:Backend|Tooling|Infrastructure|Development Tools|Specification Tooling)\s*[\r\n]+(?<sub>(?s).+?)(?=\r?\n###\s|\z)'
        }

        foreach ($Type in $SubPatterns.Keys) {
            $Pattern = $SubPatterns[$Type]
            $AllMatches = [regex]::Matches($TechSection, $Pattern)
            foreach ($M in $AllMatches) {
                $SubContent = $M.Groups['sub'].Value
                if ($Type -eq 'frontend') {
                    $TechStack.frontend = Add-Unique -Target $TechStack.frontend -Items (Get-BulletsFromSection $SubContent)
                } else {
                    $TechStack.backend = Add-Unique -Target $TechStack.backend -Items (Get-BulletsFromSection $SubContent)
                }
            }
        }

        # If we didn't find specific sub-sections but found bullets in the main section, add to backend
        if ($TechStack.frontend.Count -eq 0 -and $TechStack.backend.Count -eq 0) {
            $Bullets = Get-BulletsFromSection $TechSection
            if ($Bullets.Count -gt 0) {
                $TechStack.backend = Add-Unique -Target $TechStack.backend -Items $Bullets
            }
        }
    }

    # Extract from Markdown tables (Technical Context from plan.md)
    if ($ProjectContent -match '(?s)\| Aspect \| Value \|.*?[\r\n]+(?<table>.+?)(?=\r?\n#|\z)') {
        $TableContent = $Matches['table']
        $Rows = [regex]::Matches($TableContent, '(?m)^\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\s*\|')
        foreach ($Row in $Rows) {
            $Label = $Row.Groups[1].Value.Trim()
            $Value = $Row.Groups[2].Value.Trim()
            if ($Value -and $Value -ne '{e.g., ...}' -and $Value -notlike '*NEEDS RESEARCH*') {
                $Item = "${label}: $Value"
                $TechStack.backend = Add-Unique -Target $TechStack.backend -Items @($Item)
            }
        }
    }

    return $TechStack
}

function Test-ChecklistSequence {
    <#
    .SYNOPSIS
        Validates that CHK IDs in a checklist file are sequential without gaps.
    .PARAMETER Path
        Path to the checklist file.
    .OUTPUTS
        PSCustomObject with IsValid, Gaps, and FoundCount
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return [PSCustomObject]@{ IsValid = $True; Gaps = @(); FoundCount = 0 }
    }

    $Content = Get-Content $Path
    $Ids = @()
    foreach ($Line in $Content) {
        if ($Line -match 'CHK(\d{3})') {
            $Ids += [int]$Matches[1]
        }
    }

    if ($Ids.Count -le 1) {
        return [PSCustomObject]@{ IsValid = $True; Gaps = @(); FoundCount = $Ids.Count }
    }

    $Ids = $Ids | Sort-Object
    $Gaps = @()
    for ($I = 0; $I -lt ($Ids.Count - 1); $I++) {
        if ($Ids[$I+1] -ne ($Ids[$I] + 1)) {
            $Gaps += "Between CHK{0:D3} and CHK{1:D3}" -f $Ids[$I], $Ids[$I+1]
        }
    }

    return [PSCustomObject]@{
        IsValid = ($Gaps.Count -eq 0)
        Gaps = $Gaps
        FoundCount = $Ids.Count
    }
}

function Get-CodeConventions {
    <#
    .SYNOPSIS
        Extracts code conventions from project.md
    .PARAMETER ProjectContent
        Raw content of project.md file
    .OUTPUTS
        Array of convention names
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$ProjectContent
    )

    $Conventions = @()

    if ($ProjectContent -match '(?s)### Code Style\s*\n(.+?)(?=\n### |\z)') {
        $CodeStyleSection = $Matches[1]
        $Conventions = [regex]::Matches($CodeStyleSection, '#### ([^\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
    }

    return $Conventions
}

function Get-ArchitecturePatterns {
    <#
    .SYNOPSIS
        Extracts architecture patterns from project.md
    .PARAMETER ProjectContent
        Raw content of project.md file
    .OUTPUTS
        Array of pattern names
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$ProjectContent
    )

    $Patterns = @()

    if ($ProjectContent -match '(?s)### Architecture Patterns\s*\n(.+?)(?=\n### |\z)') {
        $ArchSection = $Matches[1]
        $Patterns = [regex]::Matches($ArchSection, '#### ([^\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
    }

    return $Patterns
}

function Get-GovernanceData {
    <#
    .SYNOPSIS
        Extracts all governance data from constitution.md and project.md
    .DESCRIPTION
        Combines extraction from constitution.md (principles, quality standards, decision framework)
        and project.md (tech stack, code conventions, architecture patterns) into a single object.

        This function replaces duplicated extraction logic in setup-document.ps1 and
        update-agent-context.ps1 (Issue #9 fix).
    .PARAMETER ConstitutionPath
        Optional. Path to constitution.md. If not provided, uses default from Get-FeaturePathsEnv.
    .PARAMETER ProjectPath
        Optional. Path to project.md. If not provided, uses default from Get-FeaturePathsEnv.
    .PARAMETER NoCache
        Optional. Force fresh read, bypass cache.
    .OUTPUTS
        PSCustomObject with: Principles, TechStack, CodeConventions, ArchitecturePatterns,
        QualityStandards, DecisionFramework, HasConstitution, HasProject
    .EXAMPLE
        $Governance = Get-GovernanceData
        $Governance.Principles | ForEach-Object { Write-Host $_.title }
    #>
    param(
        [string]$ConstitutionPath,
        [string]$ProjectPath,
        [switch]$NoCache
    )

    # Get default paths if not provided
    $EnvData = Get-FeaturePathsEnv
    if (-not $ConstitutionPath) { $ConstitutionPath = $EnvData.CONSTITUTION }
    if (-not $ProjectPath) { $ProjectPath = $EnvData.PROJECT }

    # File-based caching with 1-hour expiration
    $CacheExpiryHours = 1
    $TempDir = [System.IO.Path]::GetTempPath()
    $CacheKey = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes("$ConstitutionPath|$ProjectPath"))).Replace("-", "").ToLower()
    $CacheFile = Join-Path $TempDir "speckit-governance-cache-$CacheKey.json"

    # Check if cache is valid (exists, not expired, and files haven't changed)
    $UseCache = $False
    if (-not $NoCache -and (Test-Path $CacheFile)) {
        try {
            $CacheData = Get-Content $CacheFile -Raw | ConvertFrom-Json
            $CacheTime = [DateTime]::Parse($CacheData.Timestamp)
            $ConstitutionModTime = if (Test-Path $ConstitutionPath) { (Get-Item $ConstitutionPath).LastWriteTime } else { [DateTime]::MinValue }
            $ProjectModTime = if (Test-Path $ProjectPath) { (Get-Item $ProjectPath).LastWriteTime } else { [DateTime]::MinValue }

            # Cache is valid if:
            # 1. Less than 1 hour old
            # 2. File modification times match cached times
            if (([DateTime]::Now - $CacheTime).TotalHours -lt $CacheExpiryHours -and
                $CacheData.ConstitutionModTime -eq $ConstitutionModTime.ToString("O") -and
                $CacheData.ProjectModTime -eq $ProjectModTime.ToString("O")) {
                $UseCache = $True
            }
        } catch {
            # Invalid cache file, ignore and regenerate
        }
    }

    # Return cached data if valid
    if ($UseCache) {
        return $CacheData.Data
    }

    # Generate fresh data
    $Result = [PSCustomObject]@{
        Principles = @()
        TechStack = @{ frontend = @(); backend = @(); devtools = @() }
        CodeConventions = @()
        ArchitecturePatterns = @()
        QualityStandards = @()
        DecisionFramework = @()
        HasConstitution = $False
        HasProject = $False
        ConstitutionPath = $ConstitutionPath
        ProjectPath = $ProjectPath
    }

    # Extract from constitution.md
    if (Test-Path $ConstitutionPath) {
        $Result.HasConstitution = $True
        $ConstitutionContent = Get-Content $ConstitutionPath -Raw

        $Result.Principles = Get-Principles -ConstitutionContent $ConstitutionContent

        # Extract Quality Standards
        if ($ConstitutionContent -match '(?s)## Quality Standards\s*\n(.+?)(?=\n## |\z)') {
            $QualitySection = $Matches[1]
            $Result.QualityStandards = [regex]::Matches($QualitySection, '### ([^\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
        }

        # Extract Decision Framework
        if ($ConstitutionContent -match '(?s)## Decision Framework\s*\n(.+?)(?=\n## |\z)') {
            $DecisionSection = $Matches[1]
            $Result.DecisionFramework = [regex]::Matches($DecisionSection, '### ([^\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() }
        }
    }

    # Extract from project.md
    if (Test-Path $ProjectPath) {
        $Result.HasProject = $True
        $ProjectContent = Get-Content $ProjectPath -Raw

        $Result.TechStack = Get-TechStack -ProjectContent $ProjectContent
        $Result.CodeConventions = Get-CodeConventions -ProjectContent $ProjectContent
        $Result.ArchitecturePatterns = Get-ArchitecturePatterns -ProjectContent $ProjectContent
    }

    # Provide lower-case aliases for script consumers requiring stable keys.
    # These do not replace existing properties; they enable flexible consumption.
    try {
        $Result | Add-Member -NotePropertyName 'principles' -NotePropertyValue $Result.Principles -Force
        $Result | Add-Member -NotePropertyName 'tech_stack' -NotePropertyValue @{ frontend = @($Result.TechStack.frontend); backend = @($Result.TechStack.backend) } -Force
    } catch {
        # Non-fatal: continue without aliases
    }

    # Save to cache file
    $ConstitutionModTime = if (Test-Path $ConstitutionPath) { (Get-Item $ConstitutionPath).LastWriteTime } else { [DateTime]::MinValue }
    $ProjectModTime = if (Test-Path $ProjectPath) { (Get-Item $ProjectPath).LastWriteTime } else { [DateTime]::MinValue }

    $CacheObject = @{
        Timestamp = [DateTime]::Now.ToString("O")
        ConstitutionModTime = $ConstitutionModTime.ToString("O")
        ProjectModTime = $ProjectModTime.ToString("O")
        Data = $Result
    }

    try {
        $CacheObject | ConvertTo-Json -Depth 10 | Set-Content $CacheFile -Encoding UTF8
    } catch {
        # Non-fatal: continue without caching
    }

    return $Result
}

# =============================================================================
# DELTA OPERATIONS (T023-T027 - 001-openspec-integration)
# =============================================================================
# Functions for detecting file changes (deltas) including renamed files
# =============================================================================

function Get-RenamedFiles {
    <#
    .SYNOPSIS
        Detects renamed files using Git rename detection (T023)
    .DESCRIPTION
        Uses `git diff -M --name-status --diff-filter=R` to detect files that were renamed.
        Returns array of objects with old and new paths, plus similarity percentage.
    .PARAMETER BaseRef
        Git ref to compare against (branch, tag, or commit). Default: "main"
    .PARAMETER FeatureDir
        Optional. Limit detection to files in this directory.
    .OUTPUTS
        Array of PSCustomObjects with: OldPath, NewPath, Similarity, WasModified
    .EXAMPLE
        Get-RenamedFiles -BaseRef "main"
        Returns all renamed files compared to main branch.
    #>
    param(
        [Parameter(Position=0)]
        [string]$BaseRef = "main",

        [string]$FeatureDir
    )

    # Check Git availability
    if (-not (Test-HasGit)) {
        Write-Warning "[speckit] Git not available - RENAMED detection disabled"
        return @()
    }

    try {
        # Build git command
        $GitArgs = @("diff", "-M", "--name-status", "--diff-filter=R", $BaseRef)
        if ($FeatureDir) {
            $GitArgs += "--"
            $GitArgs += $FeatureDir
        }

        $Output = & git $GitArgs 2>$Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "[speckit] Git diff command failed - skipping rename detection"
            return @()
        }

        $Renames = @()
        foreach ($Line in $Output) {
            # Parse format: R<similarity>	old/path	new/path
            if ($Line -match '^R(\d+)\s+(.+?)\s+(.+)$') {
                $Similarity = [int]$Matches[1]
                $Renames += [PSCustomObject]@{
                    OldPath = $Matches[2].Trim()
                    NewPath = $Matches[3].Trim()
                    Similarity = $Similarity
                    WasModified = ($Similarity -lt 100)
                }
            }
        }

        return $Renames
    }
    catch {
        Write-Warning "[speckit] Error detecting renames: $_"
        return @()
    }
}

function Get-FileDeltas {
    <#
    .SYNOPSIS
        Gets all file deltas (ADDED, MODIFIED, REMOVED, RENAMED) for a feature
    .DESCRIPTION
        Comprehensive delta detection using Git. Handles all operation types
        including the combined RENAMED+MODIFIED case.
    .PARAMETER BaseRef
        Git ref to compare against. Default: "main"
    .PARAMETER FeatureDir
        Optional. Limit detection to files in this directory.
    .PARAMETER IncludeDiffContent
        Include diff content for MODIFIED files.
    .OUTPUTS
        Array of PSCustomObjects representing deltas
    #>
    param(
        [Parameter(Position=0)]
        [string]$BaseRef = "main",

        [string]$FeatureDir,

        [switch]$IncludeDiffContent
    )

    if (-not (Test-HasGit)) {
        Write-Warning "[speckit] Git not available - delta detection limited"
        return @()
    }

    $Deltas = @()
    $PathFilter = if ($FeatureDir) { @("--", $FeatureDir) } else { @() }

    try {
        # Get ADDED files
        $Added = & git diff --name-status --diff-filter=A $BaseRef @pathFilter 2>$Null
        foreach ($Line in $Added) {
            if ($Line -match '^A\s+(.+)$') {
                $Deltas += [PSCustomObject]@{
                    Operation = "ADDED"
                    Path = $Matches[1].Trim()
                    TargetPath = $Null
                    DiffSummary = $Null
                    DiffContent = $Null
                }
            }
        }

        # Get MODIFIED files
        $Modified = & git diff --name-status --diff-filter=M $BaseRef @pathFilter 2>$Null
        foreach ($Line in $Modified) {
            if ($Line -match '^M\s+(.+)$') {
                $Path = $Matches[1].Trim()
                $DiffSummary = $Null
                $DiffContent = $Null
                $IsTrivial = $False

                if ($IncludeDiffContent) {
                    # Check for whitespace-only change (T048)
                    $IsTrivial = Test-WhitespaceOnlyChange -Path $Path -BaseRef $BaseRef

                    # Get diff stats
                    $Stat = & git diff --stat $BaseRef -- $Path 2>$Null | Select-Object -Last 1
                    if ($Stat -match '(\d+)\s+insertion.*?(\d+)\s+deletion') {
                        $DiffSummary = "$($Matches[1]) insertions, $($Matches[2]) deletions"
                    } elseif ($Stat -match '(\d+)\s+insertion') {
                        $DiffSummary = "$($Matches[1]) insertions, 0 deletions"
                    } elseif ($Stat -match '(\d+)\s+deletion') {
                        $DiffSummary = "0 insertions, $($Matches[1]) deletions"
                    }

                    if ($IsTrivial) {
                        $DiffSummary = "$DiffSummary [TRIVIAL: whitespace-only]"
                    }

                    # Get diff content (first 10 lines)
                    $Diff = & git diff -U3 $BaseRef -- $Path 2>$Null | Select-Object -First 15
                    $DiffContent = $Diff -join "`n"
                }

                $Deltas += [PSCustomObject]@{
                    Operation = "MODIFIED"
                    Path = $Path
                    TargetPath = $Null
                    DiffSummary = $DiffSummary
                    DiffContent = $DiffContent
                    IsTrivial = $IsTrivial
                }
            }
        }

        # Get REMOVED files
        $Removed = & git diff --name-status --diff-filter=D $BaseRef @pathFilter 2>$Null
        foreach ($Line in $Removed) {
            if ($Line -match '^D\s+(.+)$') {
                $Deltas += [PSCustomObject]@{
                    Operation = "REMOVED"
                    Path = $Matches[1].Trim()
                    TargetPath = $Null
                    DiffSummary = $Null
                    DiffContent = $Null
                }
            }
        }

        # Get RENAMED files (includes RENAMED+MODIFIED handling)
        $Renames = Get-RenamedFiles -BaseRef $BaseRef -FeatureDir $FeatureDir
        foreach ($Rename in $Renames) {
            # Add RENAMED entry
            $Deltas += [PSCustomObject]@{
                Operation = "RENAMED"
                Path = $Rename.OldPath
                TargetPath = $Rename.NewPath
                DiffSummary = $Null
                DiffContent = $Null
            }

            # If file was also modified (similarity < 100), add MODIFIED entry
            if ($Rename.WasModified -and $IncludeDiffContent) {
                $Stat = & git diff --stat $BaseRef -- $Rename.NewPath 2>$Null | Select-Object -Last 1
                $DiffSummary = $Null
                if ($Stat -match '(\d+)\s+insertion.*?(\d+)\s+deletion') {
                    $DiffSummary = "$($Matches[1]) insertions, $($Matches[2]) deletions"
                }

                $Deltas += [PSCustomObject]@{
                    Operation = "MODIFIED"
                    Path = $Rename.NewPath
                    TargetPath = $Null
                    DiffSummary = $DiffSummary
                    DiffContent = $Null
                }
            }
        }

    }
    catch {
        Write-Warning "[speckit] Error detecting deltas: $_"
    }

    return $Deltas
}

function Format-DeltaMarkdown {
    <#
    .SYNOPSIS
        Formats delta entries as Markdown list items
    .PARAMETER Deltas
        Array of delta objects from Get-FileDeltas
    .OUTPUTS
        String array of formatted Markdown lines
    #>
    param(
        [Parameter(Mandatory=$True, ValueFromPipeline=$True)]
        [array]$Deltas
    )

    $Lines = @()
    foreach ($Delta in $Deltas) {
        switch ($Delta.Operation) {
            "ADDED" {
                $Lines += "- **ADDED**: $($Delta.Path)"
            }
            "MODIFIED" {
                if ($Delta.DiffSummary) {
                    $Lines += "- **MODIFIED**: $($Delta.Path) ($($Delta.DiffSummary))"
                } else {
                    $Lines += "- **MODIFIED**: $($Delta.Path)"
                }
            }
            "REMOVED" {
                $Lines += "- **REMOVED**: $($Delta.Path)"
            }
            "RENAMED" {
                # Use Unicode right arrow (→)
                $Lines += "- **RENAMED**: $($Delta.Path) → $($Delta.TargetPath)"
            }
        }
    }

    return $Lines
}
function Test-WhitespaceOnlyChange {
    <#
    .SYNOPSIS
        Detects if a file change is whitespace-only (trivial change)
    .DESCRIPTION
        Uses git diff with ignore whitespace options to detect trivial changes.
        A change is trivial if:
        - Only whitespace (spaces, tabs, newlines) was modified
        - No actual content was changed
    .PARAMETER Path
        File path to check
    .PARAMETER BaseRef
        Git ref to compare against. Default: "main"
    .OUTPUTS
        Boolean - $True if change is whitespace-only (trivial)
    #>
    param(
        [Parameter(Mandatory=$True)]
        [string]$Path,

        [string]$BaseRef = "main"
    )

    if (-not (Test-HasGit)) {
        return $False
    }

    try {
        # Compare with and without ignore-space option
        # If -w produces no diff but regular diff does, it's whitespace-only
        $NormalDiff = & git diff $BaseRef -- $Path 2>$Null
        $NoWhitespaceDiff = & git diff -w $BaseRef -- $Path 2>$Null

        # Has changes AND they disappear when ignoring whitespace = whitespace-only
        $HasChanges = $NormalDiff -and $NormalDiff.Length -gt 0
        $ChangesAreWhitespaceOnly = (-not $NoWhitespaceDiff) -or ($NoWhitespaceDiff.Length -eq 0)

        return ($HasChanges -and $ChangesAreWhitespaceOnly)
    }
    catch {
        Write-Verbose "[speckit] Error checking whitespace changes: $_"
        return $False
    }
}

