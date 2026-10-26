#requires -Version 5.1
[CmdletBinding()]
param(
 [ValidateSet('Earth','Mars','Other')][string]$Role='Other',
 [ValidateRange(1,600)][int]$DurationSeconds=60,
 [string]$SdkRepo,[switch]$RunIdeChecks,[switch]$CheckInstalledCompiler,
 [string]$OutputRoot=(Join-Path $env:TEMP 'VeklomEvidence')
)
$ErrorActionPreference='Stop'
$manifest=Join-Path $PSScriptRoot 'SHA256SUMS'
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw 'Package checksum manifest is missing.' }
foreach ($line in [IO.File]::ReadAllLines($manifest)) {
 if ($line -notmatch '^([a-f0-9]{64})  ([A-Za-z0-9_.-]+)$') { throw 'Invalid package checksum line.' }
 $expected=$Matches[1];$name=$Matches[2];$file=Join-Path $PSScriptRoot $name
 if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw ('Package checksum mismatch: '+$name) }
}

foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object { $_.Extension -in @('.ps1','.psm1') })) {
 $tokens=$null;$parseErrors=$null
 $null=[Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$parseErrors)
 if (@($parseErrors).Count -gt 0) { $parseErrors | Format-List Message,Extent;throw ('Parse validation failed: '+$file.Name) }
}
if ($RunIdeChecks -and [string]::IsNullOrWhiteSpace($SdkRepo)) { throw '-SdkRepo is required for -RunIdeChecks.' }
Write-Host 'Passive socket/process collection is starting. Use the normal CLI/IDE workflow in another window. No resets or stress traffic will be generated.'
$sockets=& (Join-Path $PSScriptRoot 'Collect-VeklomSockets.ps1') -Role $Role -DurationSeconds $DurationSeconds -OutputRoot $OutputRoot
Write-Host ('Return socket archive: '+$sockets.Archive)
if ($RunIdeChecks) {
 $ide=& (Join-Path $PSScriptRoot 'Test-VeklomIdeBinding.ps1') -SdkRepo $SdkRepo -CheckInstalledCompiler:$CheckInstalledCompiler -OutputRoot $OutputRoot
 Write-Host ('Return IDE archive: '+$ide.Archive)
}
