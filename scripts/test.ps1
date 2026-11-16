$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& $PSScriptRoot/start-db.ps1
$previousPgPassword=$env:PGPASSWORD
$previousDatabaseUrl=$env:DATABASE_URL
try {
$env:PGPASSWORD='tradesphere'
$exists=& .runtime/pgsql/bin/psql.exe -h 127.0.0.1 -p 54329 -U tradesphere -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='tradesphere_test'"
if ($LASTEXITCODE -ne 0) { throw 'Cannot query test database' }
if ($exists -ne '1') { & .runtime/pgsql/bin/createdb.exe -h 127.0.0.1 -p 54329 -U tradesphere tradesphere_test }
if ($LASTEXITCODE -ne 0) { throw 'Test database creation failed' }
$env:DATABASE_URL='postgresql+psycopg://tradesphere:tradesphere@127.0.0.1:54329/tradesphere_test'
  & .venv/Scripts/python.exe -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'Test database migration failed' }
  & .venv/Scripts/python.exe -m pytest backend/tests -v --junitxml=docs/evidence/pytest.xml
  if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
  npm.cmd run build --prefix frontend
  if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally { $env:DATABASE_URL=$previousDatabaseUrl; $env:PGPASSWORD=$previousPgPassword }
