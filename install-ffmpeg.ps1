<#
Installs ffmpeg for the current user.

Order of attempts:
 - If ffmpeg already on PATH, do nothing.
 - Try winget (if present).
 - Try Chocolatey (if present).
 - Download a static build and extract to $env:LOCALAPPDATA\ffmpeg and add its bin to User PATH.

Run:
  powershell -ExecutionPolicy Bypass -File .\install-ffmpeg.ps1

Note: After successful install you may need to restart your terminal (or log out/in) for PATH changes to take effect.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-ErrorMsg($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 1) Is ffmpeg already available?
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegCmd) {
    Write-Info "ffmpeg found at: $($ffmpegCmd.Source)"
    Write-Info "No installation needed."
    return 0
}

# Helper: add a directory to User PATH (if not already present)
function Add-ToUserPath($dir) {
    try {
        $dir = (Resolve-Path $dir).Path
    } catch {
        # leave as given
    }
    $current = [Environment]::GetEnvironmentVariable('Path','User') -split ';' | Where-Object { $_ -ne '' }
    if ($current -contains $dir) {
        Write-Info "Path already contains: $dir"
        return
    }
    $new = ($current + $dir) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $new, 'User')
    Write-Info "Added to User PATH: $dir"
    Write-Info "You may need to restart your terminal (or sign out/in) for changes to take effect."
}

# 2) Try winget (if present)
if (Get-Command winget -ErrorAction SilentlyContinue) {
    try {
        Write-Info "Attempting to install ffmpeg using winget..."
        # Some winget sources use the Gyan.FFmpeg ID; try a simple 'install ffmpeg' first
        winget install --silent --accept-package-agreements --accept-source-agreements --id Gyan.FFmpeg -e
        # If above succeeds, verify:
        $ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
        if ($ffmpegCmd) {
            Write-Info "ffmpeg installed via winget: $($ffmpegCmd.Source)"
            return 0
        } else {
            Write-Warn "winget install reported success but ffmpeg not on PATH yet. Continuing to other options."
        }
    } catch {
        Write-Warn "winget install failed or not available for ffmpeg: $($_.Exception.Message)"
    }
} else {
    Write-Info "winget not found, skipping."
}

# 3) Try Chocolatey (if present)
if (Get-Command choco -ErrorAction SilentlyContinue) {
    try {
        Write-Info "Attempting to install ffmpeg using Chocolatey..."
        choco install -y ffmpeg
        $ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
        if ($ffmpegCmd) {
            Write-Info "ffmpeg installed via Chocolatey: $($ffmpegCmd.Source)"
            return 0
        } else {
            Write-Warn "choco reported success but ffmpeg not found on PATH. Continuing to manual download."
        }
    } catch {
        Write-Warn "Chocolatey install failed: $($_.Exception.Message)"
    }
} else {
    Write-Info "Chocolatey not found, skipping."
}

# 4) Manual download and extract (per-user install to avoid requiring admin)
try {
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    Write-Info "Downloading ffmpeg static build from: $url"

    $tmpZip = Join-Path $env:TEMP 'ffmpeg_release.zip'
    if (Test-Path $tmpZip) { Remove-Item $tmpZip -Force }

    Invoke-WebRequest -Uri $url -OutFile $tmpZip -UseBasicParsing
    Write-Info "Downloaded to $tmpZip"

    $installRoot = Join-Path $env:LOCALAPPDATA 'ffmpeg'
    if (-Not (Test-Path $installRoot)) { New-Item -Path $installRoot -ItemType Directory | Out-Null }

    Write-Info "Extracting to $installRoot (may create a subfolder with the build name)..."
    Expand-Archive -Path $tmpZip -DestinationPath $installRoot -Force

    # Find ffmpeg.exe inside the extracted folder(s)
    $ffmpegExe = Get-ChildItem -Path $installRoot -Recurse -Filter 'ffmpeg.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $ffmpegExe) {
        Write-Warn "Could not find ffmpeg.exe after extraction. Listing extracted contents:"
        Get-ChildItem -Path $installRoot -Recurse | Select-Object FullName,Length | Format-Table -AutoSize
        throw "ffmpeg.exe not found in extracted archive."
    }

    $binDir = Split-Path $ffmpegExe.FullName -Parent
    Write-Info "ffmpeg executable found: $($ffmpegExe.FullName)"
    Write-Info "Adding '$binDir' to User PATH..."

    Add-ToUserPath $binDir

    # Clean up downloaded zip
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    Write-Info "ffmpeg installed to: $binDir"
    Write-Info "Close and re-open your terminal or sign out/in to pick up the PATH change. You can verify with 'ffmpeg -version'."
    return 0
} catch {
    Write-ErrorMsg "Automatic download/extract install failed: $($_.Exception.Message)"
    Write-ErrorMsg "You can manually download from https://www.gyan.dev/ffmpeg/builds/ and extract, then add the 'bin' folder to your PATH."
    exit 1
}
