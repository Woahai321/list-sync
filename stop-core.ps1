#!/usr/bin/env pwsh 
# PowerShell script to stop ListSync Core-Only mode

Write-Host "🛑 Stopping ListSync Core-Only Mode..." -ForegroundColor Yellow
Write-Host ""

# Stop the core-only deployment
docker-compose -f docker-compose.core.yml down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ ListSync Core stopped successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔄 To restart:" -ForegroundColor Cyan
    Write-Host "   .\start-core.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Error stopping ListSync Core" -ForegroundColor Red
    Write-Host "   Check Docker status and try again" -ForegroundColor Red
} 