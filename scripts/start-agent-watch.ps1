$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

# ── SSH Tunnel to Server 5 Ollama (167.233.202.195:11434) ──────────────────────
$sshKey = "$env:USERPROFILE\.ssh\veklom-deploy"
$tunnelArgs = @("-i", $sshKey, "-L", "11434:localhost:11434", "-N", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "root@167.233.202.195")
Write-Host "[agent-watch] Opening SSH tunnel to Server 5 Ollama..."
$tunnel = Start-Process -FilePath "ssh" -ArgumentList $tunnelArgs -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3
$tcpTest = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue
if (-not $tcpTest.TcpTestSucceeded) {
    Write-Error "[agent-watch] SSH tunnel failed. Check veklom-deploy key and Server 5 connectivity."
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "[agent-watch] Tunnel established."

# ── Canonical Ollama Config ────────────────────────────────────────────────────
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { $env:VEKLOM_AGENT_API_KEY = 'ollama' }
if (-not $env:VEKLOM_AGENT_MODEL)    { $env:VEKLOM_AGENT_MODEL = 'llama3.2:latest' }
if (-not $env:VEKLOM_AGENT_BASE_URL) { $env:VEKLOM_AGENT_BASE_URL = 'http://127.0.0.1:11434/v1' }

Write-Host "[agent-watch] Starting watch loop: model=$env:VEKLOM_AGENT_MODEL"
Set-Location $rootDir
try {
    node .\runner\watch.mjs
} finally {
    Write-Host "[agent-watch] Closing SSH tunnel (PID $($tunnel.Id))..."
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
}
