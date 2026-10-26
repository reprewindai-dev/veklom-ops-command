# ==============================================================================
# EARTH (Computer B / 192.168.2.11) LISTENER BRINGUP SCRIPT
# ==============================================================================
$ErrorActionPreference = "Continue"
$EarthDir = "C:\Users\antho\vchip"
$MarsHost = "http://192.168.2.28:8000"

if (-not (Test-Path $EarthDir)) {
    New-Item -ItemType Directory -Path $EarthDir -Force | Out-Null
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " [1] SYNCING LATEST VCHIP & VFRAC ENGINES FROM MARS ($MarsHost)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$Files = @(
    "vchip_core.py",
    "vchip_authority_server.py",
    "vchip_reality_sink.py",
    "vfrac_recursive_core.py",
    "cappo_unified_engine.py",
    "vfrac_continuum_proof_engine.py",
    "vfrac_dual_transport_cross_host.py",
    "earth_master_cross_host_runner.py"
)

foreach ($f in $Files) {
    try {
        Write-Host "  [*] Fetching $f..." -NoNewline
        Invoke-WebRequest -Uri "$MarsHost/$f" -OutFile "$EarthDir\$f" -UseBasicParsing -TimeoutSec 5
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [WARN: $($_.Exception.Message)]" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host " [2] KILLING ANY STALE PROCESSES ON PORTS 8020, 8040, 8050, 8060" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

foreach ($p in 8020, 8040, 8050, 8060) {
    $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        if ($c.OwningProcess -gt 0) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " [3] LAUNCHING EARTH GOVERNED DAEMONS (PORTS 8020, 8040, 8050, 8060)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Authority Gate (Port 8020)
Start-Process python.exe -ArgumentList "vchip_authority_server.py 8020" -WorkingDirectory $EarthDir -WindowStyle Hidden
Write-Host "  [+] Port 8020 (Authority Gate) Launched" -ForegroundColor Green

# 2. Reality Sink (Port 8040)
Start-Process python.exe -ArgumentList "vchip_reality_sink.py 8040" -WorkingDirectory $EarthDir -WindowStyle Hidden
Write-Host "  [+] Port 8040 (Reality Sink) Launched" -ForegroundColor Green

# 3. CAPPO Engine (Port 8050)
Start-Process python.exe -ArgumentList "cappo_unified_engine.py server 8050" -WorkingDirectory $EarthDir -WindowStyle Hidden
Write-Host "  [+] Port 8050 (CAPPO Unified Engine) Launched" -ForegroundColor Green

# 4. Continuum Proof Engine (Port 8060)
Start-Process python.exe -ArgumentList "vfrac_continuum_proof_engine.py server 8060" -WorkingDirectory $EarthDir -WindowStyle Hidden
Write-Host "  [+] Port 8060 (Continuum Engine) Launched" -ForegroundColor Green

Start-Sleep -Seconds 3

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host " [4] VERIFYING OPEN PORTS ON EARTH" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

$activePorts = Get-NetTCPConnection -LocalPort 8020, 8040, 8050, 8060 -State Listen -ErrorAction SilentlyContinue
$activePorts | Format-Table LocalAddress, LocalPort, State -AutoSize

if (($activePorts | Measure-Object).Count -ge 4) {
    Write-Host "`n>>> ALL 4 EARTH GOVERNED PORTS ARE OPEN AND READY FOR MARS STRIKES! <<<`n" -ForegroundColor Green
} else {
    Write-Host "`n[!] Some ports failed to start. Check active processes." -ForegroundColor Red
}
