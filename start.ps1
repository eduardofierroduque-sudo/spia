# SPIA — Production Start Script (Windows PowerShell)
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== SPIA Production Deploy ==="

if (-not $env:POSTGRES_USER -or -not $env:POSTGRES_PASSWORD -or -not $env:SPIA_API_KEY) {
  Write-Host "Setting default env vars for local testing..."
  $env:POSTGRES_USER = "spia_user"
  $env:POSTGRES_PASSWORD = "change_me_in_production"
  $env:SPIA_API_KEY = "kdBzpo_6PR-iOJxoSZbfizb3rwTf_FGIzoOqKE_0vig"
}

Write-Host "Starting services..."
docker compose -f docker-compose.prod.yml up -d --build

Write-Host ""
Write-Host "=== SPIA is running ==="
Write-Host "Frontend:  http://localhost"
Write-Host ""
Write-Host "Generate license keys: python tools/generate_license.py pro"
Write-Host ""
Write-Host "To stop: docker compose -f docker-compose.prod.yml down"
