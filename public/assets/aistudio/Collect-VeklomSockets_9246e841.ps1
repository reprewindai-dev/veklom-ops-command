#requires -Version 5.1
[CmdletBinding()]
param(
 [ValidateSet('Earth','Mars','Other')][string]$Role='Other',
 [ValidateRange(1,600)][int]$DurationSeconds=60,
 [ValidateRange(100,10000)][int]$IntervalMilliseconds=1000,
 [int[]]$Ports=@(8400,8020,8040,8050,8060,9015,9016),
 [ValidateRange(100,500000)][int]$MaxSocketRows=200000,
 [string]$OutputRoot=(Join-Path $env:TEMP 'VeklomEvidence')
)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'VeklomEvidence.psm1') -Force
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
foreach ($port in $Ports) { if ($port -lt 1 -or $port -gt 65535) { throw 'Invalid port.' } }
$dir=New-VeklomRun $OutputRoot ('sockets-'+$Role)
$meta=[ordered]@{role=$Role;started_utc=[DateTime]::UtcNow.ToString('o');powershell=$PSVersionTable.PSVersion.ToString();os_version=[Environment]::OSVersion.VersionString;is_64bit=[Environment]::Is64BitOperatingSystem;cpu_count=[Environment]::ProcessorCount;ports=$Ports;duration_requested_seconds=$DurationSeconds;interval_requested_ms=$IntervalMilliseconds;collector_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;packet_capture='NOT_PERFORMED';active_connections_created=0;processes_or_services_modified=0}
Write-VeklomJson (Join-Path $dir 'metadata.json') $meta
$encoding=[Text.UTF8Encoding]::new($false)
$socketWriter=[IO.StreamWriter]::new((Join-Path $dir 'sockets.jsonl'),$false,$encoding)
$processWriter=[IO.StreamWriter]::new((Join-Path $dir 'processes.jsonl'),$false,$encoding)
$sampleWriter=[IO.StreamWriter]::new((Join-Path $dir 'samples.jsonl'),$false,$encoding)
$errors=[Collections.Generic.List[object]]::new();$rows=0;$samples=0;$limited=$false
$watch=[Diagnostics.Stopwatch]::StartNew()
try {
 while ($watch.Elapsed.TotalSeconds -lt $DurationSeconds) {
  $tick=$watch.Elapsed.TotalMilliseconds;$utc=[DateTime]::UtcNow.ToString('o');$samples++
  try {
   $connections=@(Get-NetTCPConnection -ErrorAction Stop | Where-Object { ($Ports -contains [int]$_.LocalPort) -or ($Ports -contains [int]$_.RemotePort) })
   $states=@{}
   foreach ($connection in $connections) {
    if ($rows -ge $MaxSocketRows) { $limited=$true;break }
    $state=[string]$connection.State
    if (-not $states.ContainsKey($state)) { $states[$state]=0 }; $states[$state]++
    $creation=Get-VeklomProperty $connection 'CreationTime'
    $created=$null;if ($creation -is [DateTime]) { $created=$creation.ToUniversalTime().ToString('o') }
    $row=[ordered]@{sample=$samples;utc=$utc;elapsed_ms=[Math]::Round($watch.Elapsed.TotalMilliseconds,3);local_address=[string]$connection.LocalAddress;local_port=[int]$connection.LocalPort;remote_address=[string]$connection.RemoteAddress;remote_port=[int]$connection.RemotePort;state=$state;owning_process=[int]$connection.OwningProcess;creation_utc=$created}
    $socketWriter.WriteLine((ConvertTo-Json -InputObject $row -Compress));$rows++
   }
   foreach ($processId in @($connections | Select-Object -ExpandProperty OwningProcess -Unique)) {
    try {
     $process=Get-Process -Id ([int]$processId) -ErrorAction Stop
     $cpu=$null;try { $cpu=$process.CPU } catch { $cpu=$null }
     $p=[ordered]@{sample=$samples;utc=$utc;process_id=[int]$processId;name=$process.ProcessName;working_set_bytes=$process.WorkingSet64;private_memory_bytes=$process.PrivateMemorySize64;cpu_seconds_cumulative=$cpu;handle_count=$process.HandleCount}
     $processWriter.WriteLine((ConvertTo-Json -InputObject $p -Compress))
    } catch { $errors.Add([pscustomobject]@{sample=$samples;utc=$utc;stage='PROCESS_READ';error_type=$_.Exception.GetType().FullName}) }
   }
   $sampleWriter.WriteLine((ConvertTo-Json -InputObject ([ordered]@{sample=$samples;utc=$utc;observed_monitored_sockets=$connections.Count;states=$states;row_limit_reached=$limited}) -Depth 6 -Compress))
  } catch { $errors.Add([pscustomobject]@{sample=$samples;utc=$utc;stage='SOCKET_READ';error_type=$_.Exception.GetType().FullName});$sampleWriter.WriteLine((ConvertTo-Json -InputObject ([ordered]@{sample=$samples;utc=$utc;socket_read='FAILED'}) -Compress)) }
  $socketWriter.Flush();$processWriter.Flush();$sampleWriter.Flush()
  if ($limited) { break }
  $sleep=[Math]::Min($IntervalMilliseconds-($watch.Elapsed.TotalMilliseconds-$tick),($DurationSeconds*1000)-$watch.Elapsed.TotalMilliseconds)
  if ($sleep -gt 0) { Start-Sleep -Milliseconds ([int]$sleep) }
 }
} finally { $socketWriter.Dispose();$processWriter.Dispose();$sampleWriter.Dispose();$watch.Stop() }
Write-VeklomJson (Join-Path $dir 'errors.json') @($errors.ToArray())
$status='CAPTURED';if ($errors.Count -gt 0) { $status='CAPTURED_WITH_ERRORS' };if ($limited) { $status='ROW_LIMIT_REACHED' }
$summary=[ordered]@{status=$status;role=$Role;samples=$samples;socket_rows=$rows;errors=$errors.Count;actual_elapsed_seconds=$watch.Elapsed.TotalSeconds;packet_capture='NOT_PERFORMED';fin_rst_counts='NOT_ESTABLISHED';historical_socket_totals='NOT_ESTABLISHED';authority_enforcement='NOT_ASSESSED';committed_mutations='NOT_ASSESSED';memory_leak_claim='NOT_ASSESSED';note='Instantaneous snapshots can miss short connections. Process memory samples are not allocation/leak proof. No stress traffic or resets were generated.'}
$result=Complete-VeklomRun $dir $summary
Write-Host ('Evidence archive: '+$result.Archive)
return $result
