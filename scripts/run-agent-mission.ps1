$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

# ── Agent Environment Configuration ───────────────────────────────────────────
# The model endpoint must run on owned/local hardware (CURRENT_ARCHITECTURE_LOCK.md).
# A remote owned host is reached through its Cloudflare Tunnel; set
# VEKLOM_AGENT_BASE_URL to that endpoint. Its address is not recorded here (UNVERIFIED).
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { $env:VEKLOM_AGENT_API_KEY = 'ollama' }
if (-not $env:VEKLOM_AGENT_MODEL)    { $env:VEKLOM_AGENT_MODEL = 'llama3.2:latest' }
if (-not $env:VEKLOM_AGENT_BASE_URL) { $env:VEKLOM_AGENT_BASE_URL = 'http://127.0.0.1:11434/v1' }
# For verification missions, stop after Phase 1 alignment to avoid OOM on the 3.2B node.
# Set VEKLOM_ALIGNMENT_ONLY=false to enable Phase 2 autonomous execution.
if (-not $env:VEKLOM_ALIGNMENT_ONLY) { $env:VEKLOM_ALIGNMENT_ONLY = 'true' }

# Verify the model endpoint is reachable before spawning workers
$modelUri = [Uri]$env:VEKLOM_AGENT_BASE_URL
$tcpTest = Test-NetConnection -ComputerName $modelUri.Host -Port $modelUri.Port -WarningAction SilentlyContinue
if (-not $tcpTest.TcpTestSucceeded) {
    Write-Error "[ops-runner] Model endpoint $($modelUri.Host):$($modelUri.Port) is unreachable. Start the owned/local model server or set VEKLOM_AGENT_BASE_URL."
    exit 1
}

Write-Host "[ops-runner] Spawning workers: model=$env:VEKLOM_AGENT_MODEL base=$env:VEKLOM_AGENT_BASE_URL"

# ── Run Mission ────────────────────────────────────────────────────────────────
Set-Location (Join-Path $rootDir 'runner')
node .\runner.mjs
