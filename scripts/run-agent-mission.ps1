$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { $env:VEKLOM_AGENT_API_KEY = 'ollama' }
if (-not $env:VEKLOM_AGENT_MODEL) { $env:VEKLOM_AGENT_MODEL = 'qwen2.5:3b' }
Set-Location (Join-Path $rootDir 'runner')
node .\runner.mjs
