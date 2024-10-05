# Define the directories to be deleted
$dirsToDelete = @(".venv", "__pycache__", "dist")

# Function to recursively delete directories and specific .lock files
function Remove-DirectoriesAndLockFiles {
    param (
        [string]$path
    )

    foreach ($dir in $dirsToDelete) {
        $fullPath = Join-Path -Path $path -ChildPath $dir
        if (Test-Path -Path $fullPath) {
            if ($dir -eq ".venv") {
                # Use cmd.exe to forcefully remove .venv directory
                cmd.exe /c "rd /s /q `"$fullPath`""
            } else {
                Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    # Delete specific .lock files
    $lockFiles = @("poetry.lock", "uv.lock")
    foreach ($lockFile in $lockFiles) {
        $lockPath = Join-Path -Path $path -ChildPath $lockFile
        if (Test-Path -Path $lockPath) {
            Remove-Item -Path $lockPath -Force -ErrorAction SilentlyContinue
        }
    }

    # Recursively process subdirectories
    Get-ChildItem -Path $path -Directory | ForEach-Object {
        Remove-DirectoriesAndLockFiles -path $_.FullName
    }
}

# Get the current directory
$currentDir = Get-Location

# Start the recursive deletion process
Remove-DirectoriesAndLockFiles -path $currentDir

# Check if .venv still exists and provide a message
if (Test-Path (Join-Path -Path $currentDir -ChildPath ".venv")) {
    Write-Host "Warning: .venv directory could not be fully removed. Please close any applications using it and try again."
} else {
    Write-Host "Cleanup of directories completed successfully."
}

# Check for remaining .lock files
$remainingLockFiles = Get-ChildItem -Path $currentDir -Include "poetry.lock", "uv.lock" -File -Recurse
if ($remainingLockFiles) {
    Write-Host "Warning: Some .lock files could not be removed. Please check if they are in use."
    $remainingLockFiles | ForEach-Object {
        Write-Host "  - $($_.FullName)"
    }
} else {
    Write-Host "All specified .lock files removed successfully."
}

Write-Host "Cleanup process completed."
