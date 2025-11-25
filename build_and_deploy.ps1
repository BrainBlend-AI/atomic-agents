# Function to update version in a file
function Update-VersionInFile {
    param (
        [string]$Version,
        [string]$FilePath,
        [bool]$DryRun = $false
    )
    # Read the file content
    $content = Get-Content $FilePath
    $updated = $false
    $oldVersion = ""

    # Process each line to only update the main package version in [project] section
    $inProjectSection = $false
    for ($i = 0; $i -lt $content.Length; $i++) {
        $line = $content[$i]

        # Check if we're entering the [project] section
        if ($line -match '^\[project\]') {
            $inProjectSection = $true
        }
        # Check if we're entering a different section
        elseif ($line -match '^\[.*\]' -and $line -notmatch '^\[project\]') {
            $inProjectSection = $false
        }
        # Update version only if we're in the [project] section and it's the main version line
        elseif ($inProjectSection -and $line -match '^version = "(.+)"$') {
            $oldVersion = $matches[1]
            if (-not $DryRun) {
                $content[$i] = $line -replace 'version = ".*"', "version = `"$Version`""
            }
            $updated = $true
            break
        }
    }

    if ($updated) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would update main package version in $FilePath from $oldVersion to $Version"
        } else {
            Set-Content $FilePath $content
            Write-Host "Updated main package version in $FilePath to $Version"
        }
    } else {
        Write-Host "Warning: Could not find main package version to update in $FilePath"
    }
}

# Function to update (increment) version
function Update-Version {
    param (
        [string]$Version,
        [string]$ReleaseType
    )

    $versionParts = $Version -split '\.'
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2]

    switch ($ReleaseType) {
        "major" {
            $major++
            $minor = 0
            $patch = 0
        }
        "minor" {
            $minor++
            $patch = 0
        }
        "patch" {
            $patch++
        }
        default {
            Write-Host "Invalid release type. Use 'major', 'minor', or 'patch'."
            exit 1
        }
    }

    return "$major.$minor.$patch"
}

# Function to set PyPI token
function Set-PyPIToken {
    param (
        [bool]$DryRun = $false
    )
    if (-not $env:PYPI_TOKEN) {
        Write-Host "Error: PYPI_TOKEN environment variable is not set."
        if (-not $DryRun) {
            exit 1
        }
    }
    if ($DryRun) {
        Write-Host "[DRY RUN] Would set UV_PUBLISH_TOKEN"
    } else {
        $env:UV_PUBLISH_TOKEN = $env:PYPI_TOKEN
        Write-Host "PyPI token configured successfully."
    }
}

# Add this function at the beginning of the script
function Import-EnvFile {
    $envFile = ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $name = $matches[1]
                $value = $matches[2]
                Set-Item -Path "env:$name" -Value $value
            }
        }
        Write-Host "Environment variables loaded from .env file."
    }
    else {
        Write-Host "Warning: .env file not found."
    }
}

# Call this function before any other operations in the script
Import-EnvFile

# Parse arguments
$releaseType = ""
$dryRun = $false

foreach ($arg in $args) {
    if ($arg -eq "--dry" -or $arg -eq "--dry-run") {
        $dryRun = $true
    }
    elseif ($arg -in @("major", "minor", "patch")) {
        $releaseType = $arg
    }
    else {
        Write-Host "Unknown argument: $arg"
        Write-Host "Usage: .\build_and_deploy.ps1 <major|minor|patch> [--dry]"
        exit 1
    }
}

# Check if release type is provided
if (-not $releaseType) {
    Write-Host "Please specify a release type (major, minor, or patch)"
    Write-Host "Usage: .\build_and_deploy.ps1 <major|minor|patch> [--dry]"
    exit 1
}

# Validate release type
if ($releaseType -notin @("major", "minor", "patch")) {
    Write-Host "Invalid release type. Use 'major', 'minor', or 'patch'."
    exit 1
}

# Get current version from pyproject.toml (specifically from [project] section)
$pyprojectContent = Get-Content "pyproject.toml"
$currentVersion = ""
$inProjectSection = $false

foreach ($line in $pyprojectContent) {
    if ($line -match '^\[project\]') {
        $inProjectSection = $true
    }
    elseif ($line -match '^\[.*\]' -and $line -notmatch '^\[project\]') {
        $inProjectSection = $false
    }
    elseif ($inProjectSection -and $line -match '^version = "(.+)"$') {
        $currentVersion = $matches[1]
        break
    }
}

if (-not $currentVersion) {
    Write-Host "Error: Could not find current version in pyproject.toml [project] section"
    exit 1
}

# Calculate new version
$newVersion = Update-Version -Version $currentVersion -ReleaseType $releaseType

if ($dryRun) {
    Write-Host "[DRY RUN] Would update version from $currentVersion to $newVersion"
} else {
    Write-Host "Updating version from $currentVersion to $newVersion"
}

# Update version in files
Update-VersionInFile -Version $newVersion -FilePath "pyproject.toml" -DryRun $dryRun

if ($dryRun) {
    Write-Host "[DRY RUN] Would perform the following actions:"
    Write-Host "[DRY RUN] - Build consolidated atomic-agents package"
    Write-Host "[DRY RUN] - Install dependencies with uv sync"
    Write-Host "[DRY RUN] - Build package with uv build"
    Write-Host "[DRY RUN] - Configure PyPI token"
    Write-Host "[DRY RUN] - Upload to PyPI with uv publish"
    Write-Host "[DRY RUN] Dry run completed - no actual changes made!"
    exit 0
}

# Build the consolidated package
Write-Host "Building consolidated atomic-agents package..."

# Install dependencies
uv sync

# Build the package
uv build

# Before publishing, set the PyPI token
Set-PyPIToken -DryRun $dryRun

# Upload to PyPI
Write-Host "Uploading atomic-agents to PyPI..."
uv publish

Write-Host "Build and deploy process completed successfully!"
