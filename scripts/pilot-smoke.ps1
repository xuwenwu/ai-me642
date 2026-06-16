param(
  [int]$Port = 3000,
  [string]$InstructorEmail = "",
  [string]$InstructorPassword = ""
)

$ErrorActionPreference = "Stop"
$baseUrl = "http://127.0.0.1:$Port"

Write-Host "Checking frontend..."
$loginPage = Invoke-WebRequest "$baseUrl/login" -UseBasicParsing
Write-Host "Frontend login: HTTP $($loginPage.StatusCode)"

Write-Host "Checking backend readiness..."
$ready = Invoke-RestMethod "$baseUrl/api/health/ready"
if ($ready.status -ne "ok") {
  throw "Backend readiness returned status '$($ready.status)'."
}
Write-Host "Backend readiness: ok"

if ($InstructorEmail -and $InstructorPassword) {
  Write-Host "Checking instructor login and AI readiness..."
  $loginBody = @{ email = $InstructorEmail; password = $InstructorPassword } | ConvertTo-Json
  $session = Invoke-RestMethod "$baseUrl/api/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
  $headers = @{ Authorization = "Bearer $($session.access_token)" }
  $policy = Invoke-RestMethod "$baseUrl/api/instructor/ai-policy/readiness" -Headers $headers
  Write-Host "Instructor login: ok"
  Write-Host "AI readiness: $($policy.provider_mode), configured=$($policy.configured), model=$($policy.model)"
} else {
  Write-Host "Instructor login check skipped. Pass -InstructorEmail and -InstructorPassword to include it."
}

Write-Host "Pilot smoke checks passed."
