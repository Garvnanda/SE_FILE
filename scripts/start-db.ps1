$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$bin=Join-Path (Get-Location) '.runtime/pgsql/bin'
if (!(Test-Path "$bin/initdb.exe")) { throw 'Run scripts/setup.ps1 first.' }
if (!(Test-Path '.runtime/pgdata/PG_VERSION')) {
  'tradesphere' | Set-Content -Encoding ascii .runtime/pg-password
  & "$bin/initdb.exe" -D .runtime/pgdata -U tradesphere --pwfile=.runtime/pg-password -A scram-sha-256 -E UTF8 --locale=C
  if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed' }
  Remove-Item -LiteralPath .runtime/pg-password
}
& "$bin/pg_ctl.exe" -D .runtime/pgdata status *> $null
if ($LASTEXITCODE -ne 0) {
  & "$bin/pg_ctl.exe" -D .runtime/pgdata -l .runtime/postgres.log -o '-p 54329 -h 127.0.0.1' -w start
  if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not start; inspect .runtime/postgres.log' }
}
$previousPgPassword=$env:PGPASSWORD
try {
$env:PGPASSWORD='tradesphere'
$exists=& "$bin/psql.exe" -h 127.0.0.1 -p 54329 -U tradesphere -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='tradesphere'"
if ($LASTEXITCODE -ne 0) { throw 'Cannot query local PostgreSQL databases' }
if ($exists -ne '1') { & "$bin/createdb.exe" -h 127.0.0.1 -p 54329 -U tradesphere tradesphere }
if ($LASTEXITCODE -ne 0) { throw 'Database creation failed' }
} finally { $env:PGPASSWORD=$previousPgPassword }
