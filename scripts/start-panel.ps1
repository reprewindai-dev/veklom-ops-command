$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw 'Node.js 20+ is required. Install Node.js, then rerun this script.' }
Set-Location (Join-Path $rootDir 'panel')
& $node.Source server.mjs
