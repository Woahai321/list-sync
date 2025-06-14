# ListSync Development Launcher
# Starts all 3 services in separate terminal windows

Write-Host "🚀 Starting ListSync Development Environment..." -ForegroundColor Green
Write-Host ("=" * 50)

# Check if required directories exist
if (-not (Test-Path "data")) {
    Write-Host "❌ Data directory not found. Please run ListSync at least once to create the database." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "data/list_sync.db")) {
    Write-Host "❌ ListSync database not found. Please run ListSync at least once to create the database." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please create a .env file with your configuration." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Function to start a service in a new terminal
function Start-ServiceInNewTerminal {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory = $PWD
    )
    
    Write-Host "🔄 Starting $Title..." -ForegroundColor Yellow
    
    # Create a new PowerShell window with the command
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "& { Set-Location '$WorkingDirectory'; Write-Host '🚀 $Title' -ForegroundColor Green; Write-Host 'Working Directory: $WorkingDirectory' -ForegroundColor Cyan; $Command }"
    ) -WindowStyle Normal
    
    Start-Sleep -Seconds 2
}

# 1. Start ListSync Core Service
Write-Host "`n📊 Starting ListSync Core Service..." -ForegroundColor Cyan
Start-ServiceInNewTerminal -Title "ListSync Core Service" -Command "python -m list_sync"

# 2. Start FastAPI Backend
Write-Host "`n🔗 Starting FastAPI Backend..." -ForegroundColor Cyan
Start-ServiceInNewTerminal -Title "FastAPI Backend (Port 4222)" -Command "python start_api.py"

# 3. Start Next.js Frontend
Write-Host "`n🎨 Starting Next.js Frontend..." -ForegroundColor Cyan
$frontendPath = Join-Path $PWD "listsync-web"
Start-ServiceInNewTerminal -Title "Next.js Frontend (Port 3222)" -Command "npm run dev" -WorkingDirectory $frontendPath

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host ("=" * 50)
Write-Host "🎯 Access Points:" -ForegroundColor White
Write-Host "   📊 Dashboard:     http://localhost:3222" -ForegroundColor Cyan
Write-Host "   🔗 API Docs:      http://localhost:4222/docs" -ForegroundColor Cyan
Write-Host "   ❤️  Health Check: http://localhost:4222/api/system/health" -ForegroundColor Cyan
Write-Host "`n💡 Each service is running in its own terminal window." -ForegroundColor Yellow
Write-Host "💡 Close the terminal windows to stop the services." -ForegroundColor Yellow
Write-Host "💡 Press Ctrl+C in each terminal to gracefully stop services." -ForegroundColor Yellow

# Wait for user input before closing this window
Write-Host "`nPress any key to close this launcher window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 