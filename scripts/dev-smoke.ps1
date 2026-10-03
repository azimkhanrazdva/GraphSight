Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

ruff check .
pytest
Push-Location apps/web
npm run build
Pop-Location

