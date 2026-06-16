param(
  [int]$Port = 3000,
  [string]$ProjectName = "ai-me642-pilot",
  [string]$EnvFile = ".env.pilot",
  [switch]$RemoveContainers
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $repoRoot "docker-compose.pilot.yml"
$envPath = Join-Path $repoRoot $EnvFile
$oldPort = $env:PILOT_FRONTEND_PORT
$env:PILOT_FRONTEND_PORT = [string]$Port

try {
  if ($RemoveContainers) {
    docker compose -p $ProjectName -f $composeFile --env-file $envPath down
    Write-Host "Pilot containers stopped and removed. The named Docker volume is preserved."
  } else {
    docker compose -p $ProjectName -f $composeFile --env-file $envPath stop
    Write-Host "Pilot stack stopped. Use pilot-start.ps1 to restart it."
  }
} finally {
  $env:PILOT_FRONTEND_PORT = $oldPort
}
