Write-Host "[*] Polling Mars Gate (192.168.2.28:8020) for life..."
while ($true) {
    $tcp = Test-NetConnection -ComputerName 192.168.2.28 -Port 8020 -WarningAction SilentlyContinue
    if ($tcp.TcpTestSucceeded) {
        Write-Host "[OK] MARS GATE ONLINE. UNLEASHING 10,000-CHUNK STRIKE."
        $py = "C:\Users\antho\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        & $py -u C:\Users\antho\vchip\vfrac_traversal_strike.py http://192.168.2.28:8020 http://192.168.2.28:8040 100000
        break
    }
    Start-Sleep -Seconds 2
}
