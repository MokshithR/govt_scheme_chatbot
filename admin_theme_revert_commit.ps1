# admin_theme_revert_commit.ps1
<#
Usage: Run this script from the project root (PowerShell) to record the backup rename
of the custom admin theme in Git and commit the change.

This script attempts to run `git mv` (preferred) and then `git add -A` and commit.
If Git is not available in PATH, the script will exit with a message.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found in PATH. Install Git and re-run this script." -ForegroundColor Yellow
    exit 1
}

function Safe-GitMv($src, $dst) {
    if (Test-Path $src) {
        git mv $src $dst
        Write-Host "Renamed '$src' -> '$dst'"
    } elseif (Test-Path $dst) {
        Write-Host "Destination '$dst' already exists; skipping rename." -ForegroundColor Yellow
    } else {
        Write-Host "Neither '$src' nor '$dst' exist in repository; skipping." -ForegroundColor Yellow
    }
}

Push-Location (Get-Location)

Safe-GitMv -src 'templates/admin' -dst 'templates/admin_custom_backup'
Safe-GitMv -src 'static/admin' -dst 'static/admin_custom_backup'

Write-Host "Staging all changes..."
git add -A

$commitMessage = 'Remove custom admin theme (moved to admin_custom_backup) to restore default Django admin'

Write-Host "Committing changes with message:`n$commitMessage`n"
try {
    git commit -m "$commitMessage"
    Write-Host "Commit successful." -ForegroundColor Green
} catch {
    Write-Host "No changes to commit or commit failed: $_" -ForegroundColor Yellow
}

Pop-Location
