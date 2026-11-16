$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& .runtime/pgsql/bin/pg_ctl.exe -D .runtime/pgdata -m fast -w stop
