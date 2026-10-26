#requires -Version 5.1
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][uri]$BaseUri,
 [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_.:-]{1,128}$')][string]$EventId,
 [Parameter(Mandatory=$true)][ValidatePattern('^(sha256:)?[a-fA-F0-9]{64}$')][string]$ExpectedEventHash,
 [ValidatePattern('^[A-Za-z0-9_.:-]{1,36}$')][string]$AgentId,
 [string]$ApiKeyEnvironmentVariable='VEKLOM_PGL_API_KEY',
 [switch]$PromptForApiKey,[switch]$AllowInsecureHttp,
 [string]$OutputRoot=(Join-Path $env:TEMP 'VeklomEvidence')
)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'VeklomEvidence.psm1') -Force
if (-not $BaseUri.IsAbsoluteUri -or $BaseUri.UserInfo -or $BaseUri.Query -or $BaseUri.Fragment -or $BaseUri.AbsolutePath -ne '/') { throw 'Use an absolute ledger origin with no credentials, query, fragment or path.' }
if ($BaseUri.Scheme -ne 'https' -and -not ($BaseUri.Scheme -eq 'http' -and ($BaseUri.IsLoopback -or $AllowInsecureHttp))) { throw 'HTTPS required; non-loopback HTTP needs explicit -AllowInsecureHttp.' }
$key=[Environment]::GetEnvironmentVariable($ApiKeyEnvironmentVariable,'Process')
if ($PromptForApiKey) {
 $secure=Read-Host 'Ledger API key (not saved)' -AsSecureString
 $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
 try { $key=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer);$secure.Dispose() }
}
if ([string]::IsNullOrWhiteSpace($key) -or $key -match '[\r\n]') { throw 'No valid API key supplied. Use the environment variable or -PromptForApiKey; do not paste keys into chat.' }
$dir=New-VeklomRun $OutputRoot 'ledger-readback'
try {
 $uri=[uri]::new($BaseUri,('/api/v1/ledger/events/'+[uri]::EscapeDataString($EventId)))
 $lookup=Invoke-VeklomLedgerGet $uri $key
 $status='UNAVAILABLE';$event=$null
 if ($lookup.ok) {
  $id=Get-VeklomProperty $lookup.data 'event_id';$hash=Get-VeklomProperty $lookup.data 'event_hash';$persisted=Get-VeklomProperty $lookup.data 'persisted'
  if (($id -ceq $EventId) -and ($hash -ceq $ExpectedEventHash) -and ($persisted -is [bool]) -and $persisted) { $status='MATCH' } else { $status='MISMATCH' }
  $event=[ordered]@{event_id=$id;event_hash=$hash;persisted=$persisted;prev_event_hash=(Get-VeklomProperty $lookup.data 'prev_event_hash');event_type=(Get-VeklomProperty $lookup.data 'event_type');created_at=(Get-VeklomProperty $lookup.data 'created_at')}
 }
 $summary=[ordered]@{client_comparison=$status;event_id_requested=$EventId;expected_event_hash=$ExpectedEventHash;http_status=$lookup.http_status;error=$lookup.error;event=$event;server_chain_report='NOT_REQUESTED';event_to_agent_chain_membership='NOT_ESTABLISHED';independent_signature_verification='NOT_PERFORMED';target_effect_readback='NOT_PERFORMED';mutation_requests_sent=0;note='MATCH proves only that this authenticated read returned the expected persisted record. It does not prove the target mutation, independent signatures or inclusion in an independently verified chain.'}
 if ($AgentId) {
  $chainUri=[uri]::new($BaseUri,('/api/v1/ledger/agents/'+[uri]::EscapeDataString($AgentId)+'/verify'))
  $chain=Invoke-VeklomLedgerGet $chainUri $key
  $chainStatus=Get-VeklomProperty $chain.data 'status';$valid=Get-VeklomProperty $chain.data 'valid'
  if ($chain.ok -and $chainStatus -ceq 'verified' -and $valid -is [bool] -and $valid) { $summary.server_chain_report='SERVER_REPORTS_VALID' } else { $summary.server_chain_report='UNCONFIRMED_OR_INVALID' }
  $summary['chain_agent_id_requested']=$AgentId;$summary['chain_http_status']=$chain.http_status
 }
 $result=Complete-VeklomRun $dir $summary
 Write-Host ('Evidence archive: '+$result.Archive)
 return $result
} finally { $key=$null }
