# ListSync Development Launcher (Simple Version)
# Starts all 3 services as background jobs in the same terminal

Write-Host "🚀 Starting ListSync Development Environment (Simple Mode)..." -ForegroundColor Green
Write-Host ("=" * 60)

# Check prerequisites
if (-not (Test-Path "data/list_sync.db")) {
    Write-Host "❌ ListSync database not found. Please run ListSync at least once." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please create a .env file with your configuration." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Function to start a background job
function Start-BackgroundService {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory = $PWD
    )
    
    Write-Host "🔄 Starting $Name..." -ForegroundColor Yellow
    
    $job = Start-Job -Name $Name -ScriptBlock {
        param($cmd, $dir)
        Set-Location $dir
        Invoke-Expression $cmd
    } -ArgumentList $Command, $WorkingDirectory
    
    return $job
}

# Start services
Write-Host "`n📊 Starting services..." -ForegroundColor Cyan

# 1. Start ListSync Core
$coreJob = Start-BackgroundService -Name "ListSync-Core" -Command "python -m list_sync"

# 2. Start FastAPI Backend  
$apiJob = Start-BackgroundService -Name "ListSync-API" -Command "python start_api.py"

# 3. Start Next.js Frontend
$frontendPath = Join-Path $PWD "listsync-web"
$frontendJob = Start-BackgroundService -Name "ListSync-Frontend" -Command "npm run dev" -WorkingDirectory $frontendPath

# Wait a moment for services to start
Start-Sleep -Seconds 5

Write-Host "`n✅ All services started as background jobs!" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "🎯 Access Points:" -ForegroundColor White
Write-Host "   📊 Dashboard:     http://localhost:3222" -ForegroundColor Cyan
Write-Host "   🔗 API Docs:      http://localhost:4222/docs" -ForegroundColor Cyan
Write-Host "   ❤️  Health Check: http://localhost:4222/api/system/health" -ForegroundColor Cyan

Write-Host "`n📋 Job Status:" -ForegroundColor White
Get-Job | Format-Table -AutoSize

Write-Host "`n💡 Commands:" -ForegroundColor Yellow
Write-Host "   Get-Job                    # Check job status" -ForegroundColor Gray
Write-Host "   Receive-Job -Name <name>   # View job output" -ForegroundColor Gray
Write-Host "   Stop-Job -Name <name>      # Stop a specific job" -ForegroundColor Gray
Write-Host "   Remove-Job -Name <name>    # Remove a stopped job" -ForegroundColor Gray
Write-Host "   .\stop-dev.ps1             # Stop all services" -ForegroundColor Gray

Write-Host "`n🔄 Services are running in the background. Use the commands above to manage them." -ForegroundColor Green 