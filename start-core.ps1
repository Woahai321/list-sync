#!/usr/bin/env pwsh 
# PowerShell script to start ListSync in Core-Only mode
# This deployment includes only the core synchronization functionality
# No web UI or API server - minimal resource footprint

Write-Host "🚀 Starting ListSync Core-Only Mode..." -ForegroundColor Green
Write-Host "📦 This deployment excludes the web UI and API server" -ForegroundColor Yellow
Write-Host "🔧 Using docker-compose.core.yml configuration" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Red
    Write-Host "   Please copy .env.example to .env and configure your settings" -ForegroundColor Red
    Write-Host ""
}

# Check if Docker is running
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
} catch {
    Write-Host "❌ Error: Docker is not running or not installed" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop and try again" -ForegroundColor Red
    exit 1
}

# Start the core-only deployment
Write-Host "🐳 Starting Docker containers..." -ForegroundColor Blue
docker-compose -f docker-compose.core.yml up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ ListSync Core started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Core Status:" -ForegroundColor Cyan
    Write-Host "   • Container: listsync-core" -ForegroundColor White
    Write-Host "   • Mode: Headless sync only" -ForegroundColor White
    Write-Host "   • Web UI: Not available (core mode)" -ForegroundColor White
    Write-Host "   • API Server: Not available (core mode)" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 View logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose -f docker-compose.core.yml logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 To stop:" -ForegroundColor Cyan
    Write-Host "   docker-compose -f docker-compose.core.yml down" -ForegroundColor White
    Write-Host "   or run: .\stop-core.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Failed to start ListSync Core" -ForegroundColor Red
    Write-Host "   Check the logs above for error details" -ForegroundColor Red
} 