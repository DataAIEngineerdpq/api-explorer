# start.ps1 - Daily startup for API Explorer.
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"

# 1. Check Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Start Docker Desktop and wait for 'Engine running'." -ForegroundColor Red
    exit 1
}

# 2. Start the database container
Write-Host "Starting database container..." -ForegroundColor Cyan
docker compose up -d

# 3. Wait until Postgres actually accepts connections
Write-Host "Waiting for Postgres to be ready..." -ForegroundColor Cyan
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    docker exec api-explorer-db pg_isready -U postgres -d api_explorer *> $null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $ready) {
    Write-Host "Postgres did not become ready in time. Check: docker compose logs db" -ForegroundColor Red
    exit 1
}
Write-Host "Postgres is ready." -ForegroundColor Green

# 4. Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "No venv found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}
& ".\venv\Scripts\Activate.ps1"

# 5. Launch the API
Write-Host "Starting FastAPI on http://localhost:8000" -ForegroundColor Green
uvicorn main:app --reload