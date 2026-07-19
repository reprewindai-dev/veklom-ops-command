$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { throw 'Set VEKLOM_AGENT_API_KEY or OPENAI_API_KEY before starting the agent watch.' }
if (-not $env:VEKLOM_AGENT_MODEL) { throw 'Set VEKLOM_AGENT_MODEL before starting the agent watch.' }
Set-Location $rootDir
node .\runner\watch.mjs
