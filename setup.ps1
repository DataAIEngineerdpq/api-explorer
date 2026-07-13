# setup.ps1 - One-time setup for API Explorer.
# Usage: .\setup.ps1  (run once after cloning the repo)

$ErrorActionPreference = "Stop"

# 1. Create the virtual environment if missing
if (Test-Path ".\venv") {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# 2. Activate it
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# 3. Install dependencies
Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Make sure Ollama is installed and the models are pulled:" -ForegroundColor Yellow
Write-Host "  ollama pull qwen2.5-coder:7b" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then run: .\start.ps1" -ForegroundColor Green