# SongSensei MVP - Testing Setup (PowerShell)
Write-Host "SongSensei MVP - Testing Setup" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Check if Docker is running
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is running" -ForegroundColor Green
    } else {
        Write-Host "Docker is not running. Please start Docker first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Docker is not installed or not available. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if required files exist
$RequiredFiles = @(
    "docker-compose.yml",
    "Makefile", 
    "README.md",
    "api/package.json",
    "api/Dockerfile",
    "web/package.json",
    "web/Dockerfile",
    "analysis/requirements.txt",
    "analysis/Dockerfile",
    "analysis/main.py"
)

Write-Host ""
Write-Host "Checking required files..." -ForegroundColor Yellow

$allFilesExist = $true
foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Host "Found: $file" -ForegroundColor Green
    } else {
        Write-Host "Missing: $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "Some required files are missing. Please ensure all files are in place." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Ready to build and run SongSensei MVP!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: make build" -ForegroundColor White
Write-Host "2. Run: make up" -ForegroundColor White
Write-Host "3. Open: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Services will be available at:" -ForegroundColor Cyan
Write-Host "- Web UI: http://localhost:3000" -ForegroundColor White
Write-Host "- API: http://localhost:4000" -ForegroundColor White
Write-Host "- Analysis Service: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "If you don't have make installed on Windows, you can run:" -ForegroundColor Yellow
Write-Host "   docker-compose build" -ForegroundColor White
Write-Host "   docker-compose up" -ForegroundColor White
