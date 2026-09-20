Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Starting Tamil and Multilingual News Truth Checker..." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
