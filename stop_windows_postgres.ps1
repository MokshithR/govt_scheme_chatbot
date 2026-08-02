# =========================================================
# STOP WINDOWS POSTGRESQL SERVICE
# =========================================================
# This script stops and disables the Windows PostgreSQL service
# so Django can connect to Docker PostgreSQL on port 5432.
#
# IMPORTANT: Run this script AS ADMINISTRATOR
# Right-click PowerShell -> "Run as Administrator"
# =========================================================

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "STOPPING WINDOWS POSTGRESQL SERVICE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# Service name
$serviceName = "postgresql-x64-18"

# Check if service exists
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "WARNING: Service '$serviceName' not found!" -ForegroundColor Yellow
    Write-Host "Checking for other PostgreSQL services..." -ForegroundColor Yellow
    Write-Host ""
    Get-Service | Where-Object {$_.Name -like "*postgres*"} | Format-Table Name, Status, DisplayName
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found service: $($service.DisplayName)" -ForegroundColor Green
Write-Host "Current status: $($service.Status)" -ForegroundColor Yellow
Write-Host ""

# Stop the service
Write-Host "Step 1: Stopping service..." -ForegroundColor Cyan
try {
    Stop-Service -Name $serviceName -Force -ErrorAction Stop
    Write-Host "[OK] Service stopped successfully" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Failed to stop service: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Wait a moment for service to fully stop
Start-Sleep -Seconds 2

# Disable the service (prevent auto-start on reboot)
Write-Host ""
Write-Host "Step 2: Disabling service (prevents auto-start)..." -ForegroundColor Cyan
try {
    Set-Service -Name $serviceName -StartupType Disabled -ErrorAction Stop
    Write-Host "[OK] Service disabled successfully" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Failed to disable service: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Verify the changes
Write-Host ""
Write-Host "Step 3: Verifying changes..." -ForegroundColor Cyan
$updatedService = Get-Service -Name $serviceName
Write-Host "  Status: $($updatedService.Status)" -ForegroundColor $(if ($updatedService.Status -eq 'Stopped') {'Green'} else {'Red'})
Write-Host "  Startup Type: $($updatedService.StartType)" -ForegroundColor $(if ($updatedService.StartType -eq 'Disabled') {'Green'} else {'Red'})

# Check port 5432
Write-Host ""
Write-Host "Step 4: Checking port 5432..." -ForegroundColor Cyan
$port5432 = netstat -ano | Select-String ":5432" | Select-String "LISTENING"

if ($port5432) {
    Write-Host "  Port 5432 status:" -ForegroundColor Yellow
    $port5432 | ForEach-Object {
        $line = $_.Line
        if ($line -match "(\d+)\s*$") {
            $procId = $matches[1]
            $processName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
            Write-Host "    PID $procId ($processName)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  [OK] Port 5432 is free" -ForegroundColor Green
}

# Check Docker container
Write-Host ""
Write-Host "Step 5: Verifying Docker PostgreSQL container..." -ForegroundColor Cyan
$dockerContainer = docker ps --filter "name=pgvector" --format "{{.Names}}: {{.Status}}"

if ($dockerContainer) {
    Write-Host "  [OK] $dockerContainer" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Docker container 'pgvector' not running!" -ForegroundColor Yellow
    Write-Host "  Start it with: docker start pgvector" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "[OK] Windows PostgreSQL stopped and disabled" -ForegroundColor Green
Write-Host "[OK] Port 5432 should now be available for Docker PostgreSQL" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Restart Docker container if needed: docker restart pgvector" -ForegroundColor White
Write-Host "2. Test connection with: python test_docker_postgres_connection.py" -ForegroundColor White
Write-Host "3. Run Django migrations: python manage.py migrate" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
