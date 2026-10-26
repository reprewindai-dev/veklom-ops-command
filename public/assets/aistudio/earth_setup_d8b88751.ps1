# --- EARTH (Computer B) FILE SYNC & SERVICE LAUNCHER ---
$EarthDir   = "C:\Users\antho\vchip"
$MarsHost   = "http://192.168.2.28:8000"
$PythonPath = "C:\Users\antho\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (-not (Test-Path $EarthDir)) { New-Item -ItemType Directory -Path $EarthDir -Force }

Write-Host "[+] Syncing Engine Files from Mars ($MarsHost)..." -ForegroundColor Green

$Files = @(
    "vchip_core.py",
    "vchip_authority_server.py",
    "vchip_reality_sink.py",
    "vfrac_recursive_core.py",
    "cappo_unified_engine.py",
    "vfrac_continuum_proof_engine.py"
)

foreach ($f in $Files) {
    Write-Host "[*] Downloading $f..." -ForegroundColor Cyan
    # Use curl.exe to avoid PowerShell OOM memory spikes
    curl.exe -f -s -o "$EarthDir\$f" "$MarsHost/$f"
}

Write-Host "[+] Download Complete! Launching Earth Listeners on 8020, 8040, 8050, 8060..." -ForegroundColor Green

Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vchip_authority_server.py 8020" -WorkingDirectory $EarthDir -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vchip_reality_sink.py 8040" -WorkingDirectory $EarthDir -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\cappo_unified_engine.py server 8050" -WorkingDirectory $EarthDir -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vfrac_continuum_proof_engine.py server 8060" -WorkingDirectory $EarthDir -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "[*] Verifying Earth Port Readiness:" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8020, 8040, 8050, 8060 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State
