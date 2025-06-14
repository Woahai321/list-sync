@echo off
echo 🚀 Starting ListSync Development Environment...
echo ============================================================

REM Check prerequisites
if not exist "data\list_sync.db" (
    echo ❌ ListSync database not found. Please run ListSync at least once.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ❌ .env file not found. Please create a .env file with your configuration.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Start services in separate windows
echo.
echo 📊 Starting ListSync Core Service...
start "ListSync Core Service" cmd /k "python -m list_sync"

echo.
echo 🔗 Starting FastAPI Backend...
start "FastAPI Backend (Port 4222)" cmd /k "python start_api.py"

echo.
echo 🎨 Starting Next.js Frontend...
start "Next.js Frontend (Port 3222)" cmd /k "cd listsync-web && npm run dev"

echo.
echo ✅ All services started!
echo ============================================================
echo 🎯 Access Points:
echo    📊 Dashboard:     http://localhost:3222
echo    🔗 API Docs:      http://localhost:4222/docs
echo    ❤️  Health Check: http://localhost:4222/api/system/health
echo.
echo 💡 Each service is running in its own command window.
echo 💡 Close the command windows to stop the services.
echo 💡 Press Ctrl+C in each window to gracefully stop services.
echo.
pause 