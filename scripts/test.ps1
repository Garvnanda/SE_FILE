$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& $PSScriptRoot/start-db.ps1
$env:PGPASSWORD='tradesphere'
$exists=& .runtime/pgsql/bin/psql.exe -h 127.0.0.1 -p 54329 -U tradesphere -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='tradesphere_test'"
if ($exists -ne '1') { & .runtime/pgsql/bin/createdb.exe -h 127.0.0.1 -p 54329 -U tradesphere tradesphere_test }
$env:DATABASE_URL='postgresql+psycopg://tradesphere:tradesphere@127.0.0.1:54329/tradesphere_test'
try {
  & .venv/Scripts/python.exe -m alembic upgrade head
  & .venv/Scripts/python.exe -m pytest backend/tests -v --junitxml=docs/evidence/pytest.xml
  if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
  npm.cmd run build --prefix frontend
  if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally { Remove-Item Env:DATABASE_URL; Remove-Item Env:PGPASSWORD }
