$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

# ── SSH Tunnel to Server 5 Ollama (167.233.202.195:11434) ──────────────────────
# Opens a local port-forward so agents can reach Ollama via 127.0.0.1:11434.
# Uses the canonical veklom-deploy key. Requires OpenSSH to be in PATH.
$sshKey = "$env:USERPROFILE\.ssh\veklom-deploy"
$tunnelArgs = @("-i", $sshKey, "-L", "11434:localhost:11434", "-N", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "root@167.233.202.195")

Write-Host "[ops-runner] Opening SSH tunnel to Server 5 Ollama..."
$tunnel = Start-Process -FilePath "ssh" -ArgumentList $tunnelArgs -PassThru -WindowStyle Hidden

# Give the tunnel a moment to establish
Start-Sleep -Seconds 3

# Verify the tunnel port is reachable before spawning workers
$tcpTest = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue
if (-not $tcpTest.TcpTestSucceeded) {
    Write-Error "[ops-runner] SSH tunnel failed to open port 11434. Check SSH key and Server 5 connectivity."
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "[ops-runner] Tunnel established. 127.0.0.1:11434 -> 167.233.202.195:11434"

# ── Agent Environment Configuration ───────────────────────────────────────────
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { $env:VEKLOM_AGENT_API_KEY = 'ollama' }
if (-not $env:VEKLOM_AGENT_MODEL)    { $env:VEKLOM_AGENT_MODEL = 'llama3.2:latest' }
if (-not $env:VEKLOM_AGENT_BASE_URL) { $env:VEKLOM_AGENT_BASE_URL = 'http://127.0.0.1:11434/v1' }
# For verification missions, stop after Phase 1 alignment to avoid OOM on the 3.2B node.
# Set VEKLOM_ALIGNMENT_ONLY=false to enable Phase 2 autonomous execution.
if (-not $env:VEKLOM_ALIGNMENT_ONLY) { $env:VEKLOM_ALIGNMENT_ONLY = 'true' }

Write-Host "[ops-runner] Spawning workers: model=$env:VEKLOM_AGENT_MODEL base=$env:VEKLOM_AGENT_BASE_URL"

# ── Run Mission ────────────────────────────────────────────────────────────────
Set-Location (Join-Path $rootDir 'runner')
try {
    node .\runner.mjs
} finally {
    # Always kill the tunnel when the runner exits (success or failure)
    Write-Host "[ops-runner] Closing SSH tunnel (PID $($tunnel.Id))..."
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
}
