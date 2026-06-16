param(
  [int]$Port = 3000,
  [string]$ProjectName = "ai-me642-pilot",
  [string]$EnvFile = ".env.pilot"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $repoRoot "docker-compose.pilot.yml"
$envPath = Join-Path $repoRoot $EnvFile
$oldPort = $env:PILOT_FRONTEND_PORT
$env:PILOT_FRONTEND_PORT = [string]$Port

try {
  docker compose -p $ProjectName -f $composeFile --env-file $envPath ps
  Write-Host ""
  Write-Host "Checking frontend login page..."
  $login = Invoke-WebRequest "http://127.0.0.1:$Port/login" -UseBasicParsing
  Write-Host "Frontend: HTTP $($login.StatusCode)"
  Write-Host "Checking backend readiness through frontend proxy..."
  $ready = Invoke-RestMethod "http://127.0.0.1:$Port/api/health/ready"
  $ready | ConvertTo-Json -Depth 6
  Write-Host ""
  Write-Host "Workstation URL: http://127.0.0.1:$Port/login"
} finally {
  $env:PILOT_FRONTEND_PORT = $oldPort
}
