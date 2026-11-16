$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check { if ($LASTEXITCODE -ne 0) { throw 'Setup command failed. See output above.' } }
if (!(Test-Path .venv/Scripts/python.exe)) { python -m venv .venv; Check }
& .venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt; Check
npm.cmd ci --prefix frontend; Check
New-Item -ItemType Directory -Force .runtime | Out-Null
if (!(Test-Path .runtime/pgsql/bin/initdb.exe)) {
  if (!(Test-Path .runtime/postgres.zip)) {
    curl.exe -L --fail https://get.enterprisedb.com/postgresql/postgresql-17.6-1-windows-x64-binaries.zip -o .runtime/postgres.zip; Check
  }
  & .venv/Scripts/python.exe scripts/extract_postgres.py; Check
}
if (!(Test-Path .env)) { Copy-Item .env.example .env }
& $PSScriptRoot/start-db.ps1
& .venv/Scripts/python.exe -m alembic upgrade head; Check
& .venv/Scripts/python.exe scripts/seed_demo.py; Check
npm.cmd run build --prefix frontend; Check
Write-Host 'Ready. Run scripts/start.ps1 and open http://127.0.0.1:8000. Credentials: .runtime/demo-accounts.json'
