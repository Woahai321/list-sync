# ListSync Development Stopper
# Stops all running ListSync development services

Write-Host "🛑 Stopping ListSync Development Services..." -ForegroundColor Red
Write-Host ("=" * 50)

# Get all ListSync related jobs
$jobs = Get-Job | Where-Object { $_.Name -like "*ListSync*" }

if ($jobs.Count -eq 0) {
    Write-Host "ℹ️  No ListSync jobs found running." -ForegroundColor Yellow
} else {
    Write-Host "📋 Found $($jobs.Count) ListSync job(s):" -ForegroundColor Cyan
    $jobs | Format-Table -Property Name, State, HasMoreData -AutoSize
    
    Write-Host "`n🔄 Stopping jobs..." -ForegroundColor Yellow
    
    foreach ($job in $jobs) {
        Write-Host "   Stopping $($job.Name)..." -ForegroundColor Gray
        Stop-Job -Job $job -PassThru | Out-Null
        Remove-Job -Job $job -Force
    }
    
    Write-Host "✅ All ListSync services stopped and cleaned up." -ForegroundColor Green
}

# Also try to kill any remaining processes on the ports
Write-Host "`n🔍 Checking for processes on ports 3222 and 4222..." -ForegroundColor Cyan

try {
    # Check port 3222 (Next.js)
    $port3000 = Get-NetTCPConnection -LocalPort 3222 -ErrorAction SilentlyContinue
    if ($port3000) {
        Write-Host "   Found process on port 3222, attempting to stop..." -ForegroundColor Yellow
        $process3000 = Get-Process -Id $port3000.OwningProcess -ErrorAction SilentlyContinue
        if ($process3000) {
            Stop-Process -Id $process3000.Id -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ Stopped process on port 3222" -ForegroundColor Green
        }
    }
    
    # Check port 4222 (FastAPI)
    $port3001 = Get-NetTCPConnection -LocalPort 4222 -ErrorAction SilentlyContinue
    if ($port3001) {
        Write-Host "   Found process on port 4222, attempting to stop..." -ForegroundColor Yellow
        $process3001 = Get-Process -Id $port3001.OwningProcess -ErrorAction SilentlyContinue
        if ($process3001) {
            Stop-Process -Id $process3001.Id -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ Stopped process on port 4222" -ForegroundColor Green
        }
    }
    
    if (-not $port3000 -and -not $port3001) {
        Write-Host "   ℹ️  No processes found on ports 3222 or 4222" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not check ports (this is normal if no processes are running)" -ForegroundColor Yellow
}

Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
Write-Host "💡 You can now run .\start-dev.ps1 to start services again." -ForegroundColor Cyan 