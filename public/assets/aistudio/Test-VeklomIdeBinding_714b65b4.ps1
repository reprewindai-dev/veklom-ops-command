#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SdkRepo,[switch]$CheckInstalledCompiler,[string]$OutputRoot=(Join-Path $env:TEMP 'VeklomEvidence'))
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'VeklomEvidence.psm1') -Force
$repo=(Resolve-Path -LiteralPath $SdkRepo).Path
$target=Join-Path $repo 'src\workspace.ts'
$outputFull=[IO.Path]::GetFullPath($OutputRoot).TrimEnd('\')
if ($outputFull.Equals($repo.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase) -or $outputFull.StartsWith($repo.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Choose an output directory outside the SDK checkout.' }
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'SDK src/workspace.ts was not found.' }
$dir=New-VeklomRun $OutputRoot 'ide-binding'
$original=[IO.File]::ReadAllText($target).Replace("`r`n","`n")
$blob=Get-VeklomBlob $original
$rawHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
$summary=[ordered]@{source_git_blob=$blob;source_raw_sha256=$rawHash;status='NOT_RUN';baseline=$null;patched=$null;compiler_status='NOT_REQUESTED';scope='ISOLATED_RESOLVER_NOT_EXTENSION_HOST';repository_files_modified=0}
if ($blob -ne '8a67d894a10564fe5999b6aa2e447b5ac79ed9ac') {
 $summary.status='SOURCE_REVISION_MISMATCH';$result=Complete-VeklomRun $dir $summary;Write-Host ('Return this revision report: '+$result.Archive);return $result
}
$node=Get-Command node -CommandType Application -ErrorAction SilentlyContinue
if ($null -eq $node) { $summary.status='NODE_NOT_INSTALLED';$result=Complete-VeklomRun $dir $summary;Write-Host $result.Archive;return $result }
$old='  const folder = vscode.workspace.workspaceFolders?.find(item => item.uri.toString() === context.rootUri)' + "`n" + '    ?? vscode.workspace.workspaceFolders?.[0];'
$new='  const folder = vscode.workspace.workspaceFolders?.find(item => item.uri.toString() === context.rootUri);'
if (-not $original.Contains($old)) { throw 'Reviewed patch context did not match; refusing to guess.' }
$patched=$original.Replace($old,$new)
foreach ($variant in @('baseline','patched')) {
 $copy=Join-Path $dir $variant
 $null=New-Item -ItemType Directory -Path (Join-Path $copy 'src') -Force
 $null=New-Item -ItemType Directory -Path (Join-Path $copy 'scripts') -Force
 $text=$original;if ($variant -eq 'patched') { $text=$patched }
 [IO.File]::WriteAllText((Join-Path $copy 'src\workspace.ts'),$text,[Text.UTF8Encoding]::new($false))
 Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'workspace-binding.test.mjs') -Destination (Join-Path $copy 'scripts\workspace-binding.test.mjs')
 $run=Invoke-VeklomNative $node.Source '--test scripts/workspace-binding.test.mjs' $copy (Join-Path $dir $variant) 30
 $summary[$variant]=$run
}
$baselineLog=[IO.File]::ReadAllText((Join-Path $dir 'baseline.stdout.txt'))
$patchedLog=[IO.File]::ReadAllText((Join-Path $dir 'patched.stdout.txt'))
if (-not $summary.baseline.timed_out -and -not $summary.patched.timed_out -and $summary.baseline.exit_code -ne 0 -and $summary.patched.exit_code -eq 0 -and $baselineLog -match '# fail 4(?:\r?\n|$)' -and $patchedLog -match '# pass 14(?:\r?\n|$)' -and $patchedLog -match '# fail 0(?:\r?\n|$)') { $summary.status='EXPECTED_RED_GREEN_REPRODUCED' } else { $summary.status='RED_GREEN_NOT_ESTABLISHED' }
if ($CheckInstalledCompiler) {
 $compiler=Join-Path $repo 'node_modules\typescript\bin\tsc'
 if (Test-Path -LiteralPath $compiler -PathType Leaf) {
  $args='"'+$compiler+'" --noEmit --incremental false -p .'
  $compile=Invoke-VeklomNative $node.Source $args $repo (Join-Path $dir 'compiler') 120
  $summary['compiler']=$compile
  if ($compile.exit_code -eq 0 -and -not $compile.timed_out) { $summary.compiler_status='ORIGINAL_CHECKOUT_TYPECHECK_PASSED' } else { $summary.compiler_status='ORIGINAL_CHECKOUT_TYPECHECK_FAILED' }
 } else { $summary.compiler_status='DEPENDENCIES_NOT_INSTALLED_NO_INSTALL_ATTEMPTED' }
}
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $rawHash) { $summary.status='ORIGINAL_SOURCE_CHANGED_DURING_CHECK' }
$summary['node_executable_sha256']=(Get-FileHash -LiteralPath $node.Source -Algorithm SHA256).Hash
$summary['note']='Compiler, if requested, checks the original checkout. The temporary patched resolver tests are not a full patched SDK build, live authorization, containment, replay or ledger test.'
$result=Complete-VeklomRun $dir $summary
Write-Host ('Evidence archive: '+$result.Archive)
return $result
