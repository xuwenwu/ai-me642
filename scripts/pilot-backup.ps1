param(
  [int]$Port = 3000,
  [string]$ProjectName = "ai-me642-pilot",
  [string]$EnvFile = ".env.pilot",
  [string]$Destination = "pilot_backups"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $repoRoot "docker-compose.pilot.yml"
$envPath = Join-Path $repoRoot $EnvFile
$destinationPath = Join-Path $repoRoot $Destination
New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null

$oldPort = $env:PILOT_FRONTEND_PORT
$env:PILOT_FRONTEND_PORT = [string]$Port
try {
  docker compose -p $ProjectName -f $composeFile --env-file $envPath exec -T backend python scripts/backup_local_data.py
  $container = docker compose -p $ProjectName -f $composeFile --env-file $envPath ps -q backend
  if (-not $container) {
    throw "Could not find the backend container for project $ProjectName."
  }
  $latest = docker compose -p $ProjectName -f $composeFile --env-file $envPath exec -T backend python -c "import glob, os; files=glob.glob('/data/backups/*.zip'); print(max(files, key=os.path.getmtime) if files else '')"
  $latest = $latest.Trim()
  if (-not $latest) {
    throw "No backup ZIP was found in /data/backups after running backup_local_data.py."
  }
  $localPath = Join-Path $destinationPath (Split-Path $latest -Leaf)
  docker cp "${container}:$latest" $localPath
  Write-Host "Backup copied to: $localPath"
} finally {
  $env:PILOT_FRONTEND_PORT = $oldPort
}
