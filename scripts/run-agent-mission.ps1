$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
if (-not $env:VEKLOM_AGENT_API_KEY -and -not $env:OPENAI_API_KEY) { throw 'Set VEKLOM_AGENT_API_KEY or OPENAI_API_KEY before running the agent runner.' }
if (-not $env:VEKLOM_AGENT_MODEL) { throw 'Set VEKLOM_AGENT_MODEL before running the agent runner.' }
Set-Location (Join-Path $rootDir 'runner')
node .\runner.mjs
