param(
  [int]$Port = 3000,
  [string]$ProjectName = "ai-me642-pilot",
  [string]$EnvFile = ".env.pilot",
  [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $repoRoot "docker-compose.pilot.yml"
$envPath = Join-Path $repoRoot $EnvFile

if (-not (Test-Path $envPath)) {
  throw "Missing $EnvFile. Copy .env.pilot.example to .env.pilot and set course secrets before starting the pilot."
}

$oldPort = $env:PILOT_FRONTEND_PORT
$env:PILOT_FRONTEND_PORT = [string]$Port
try {
  $composeArgs = @("compose", "-p", $ProjectName, "-f", $composeFile, "--env-file", $envPath, "up", "-d")
  if (-not $NoBuild) {
    $composeArgs += "--build"
  }
  docker @composeArgs
  Write-Host ""
  Write-Host "Pilot stack started."
  Write-Host "Workstation URL: http://127.0.0.1:$Port/login"
  Write-Host "Status command: .\scripts\pilot-status.ps1 -Port $Port -ProjectName $ProjectName"
} finally {
  $env:PILOT_FRONTEND_PORT = $oldPort
}
