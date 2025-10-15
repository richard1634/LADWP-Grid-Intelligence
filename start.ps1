# LADWP Grid Intelligence Dashboard - Startup Script
# This script starts both the backend (FastAPI) and frontend (React) servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LADWP Grid Intelligence Dashboard v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Python found" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
Write-Host "[2/4] Checking Node.js..." -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Node.js found: $(node --version)" -ForegroundColor Green
} else {
    Write-Host "  ✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if frontend dependencies are installed
Write-Host "[3/4] Checking frontend dependencies..." -ForegroundColor Yellow
if (Test-Path "frontend/node_modules") {
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Set-Location ..
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
}

Write-Host "[4/4] Starting servers..." -ForegroundColor Yellow
Write-Host ""

# Start backend in new window using uvicorn
Write-Host "Starting Backend (FastAPI) on port 8000..." -ForegroundColor Cyan
$scriptPath = $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload"

# Wait a moment for backend to start
Start-Sleep -Seconds 5

# Start frontend in new window using vite directly
Write-Host "Starting Frontend (React/Vite)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\frontend'; node .\node_modules\vite\bin\vite.js"

# Wait for servers to initialize
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Both servers started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:5175 (or check Vite terminal)" -ForegroundColor White
Write-Host ""
Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:5175"
Write-Host ""
Write-Host "Close the PowerShell windows to stop the servers" -ForegroundColor Yellow
Write-Host ""
