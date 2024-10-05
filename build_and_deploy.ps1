# Function to update version in a file
function Update-VersionInFile {
    param (
        [string]$Version,
        [string]$FilePath
    )
    (Get-Content $FilePath) -replace 'version = ".*"', "version = `"$Version`"" | Set-Content $FilePath
    Write-Host "Updated version in $FilePath to $Version"
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
    if (-not $env:PYPI_TOKEN) {
        Write-Host "Error: PYPI_TOKEN environment variable is not set."
        exit 1
    }
    poetry config pypi-token.pypi $env:PYPI_TOKEN
    Write-Host "PyPI token configured successfully."
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

# Check if release type is provided
if ($args.Count -eq 0) {
    Write-Host "Please specify a release type (major, minor, or patch)"
    exit 1
}

$releaseType = $args[0]

# Validate release type
if ($releaseType -notin @("major", "minor", "patch")) {
    Write-Host "Invalid release type. Use 'major', 'minor', or 'patch'."
    exit 1
}

# Get current version from pyproject.toml
$currentVersion = (Select-String -Path "pyproject.toml" -Pattern 'version = "(.+)"').Matches.Groups[1].Value

# Calculate new version
$newVersion = Update-Version -Version $currentVersion -ReleaseType $releaseType

Write-Host "Updating version from $currentVersion to $newVersion"

# Update version in files
Update-VersionInFile -Version $newVersion -FilePath "pyproject.toml"

# Build the consolidated package
Write-Host "Building consolidated atomic-agents package..."

# Create a new virtualenv in the project directory and install dependencies
poetry install

# Build the package
poetry build

# Before publishing, set the PyPI token
Set-PyPIToken

# Upload to PyPI
Write-Host "Uploading atomic-agents to PyPI..."
# poetry publish

Write-Host "Build and deploy process completed successfully!"
