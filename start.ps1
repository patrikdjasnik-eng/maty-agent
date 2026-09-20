$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
  Write-Host "Chybi .env. Zkopiruj .env.example jako .env a dopln prihlaseni k emailu."
  exit 1
}

python -m app.main
