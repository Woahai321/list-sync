@echo off
echo 🛑 Stopping ListSync Development Services...
echo ============================================================

echo 🔍 Stopping processes on ports 3222 and 4222...

REM Kill processes using ports 3222 and 4222
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3222') do (
    if not "%%a"=="0" (
        echo Stopping process %%a on port 3222...
        taskkill /PID %%a /F >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4222') do (
    if not "%%a"=="0" (
        echo Stopping process %%a on port 4222...
        taskkill /PID %%a /F >nul 2>&1
    )
)

REM Also kill any remaining node.exe and python.exe processes
echo 🔄 Cleaning up remaining processes...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

echo ✅ All services stopped!
echo 💡 You can now run start-dev.bat to start services again.
pause 