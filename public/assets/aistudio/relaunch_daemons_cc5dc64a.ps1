$EarthDir   = "C:\Users\antho\vchip"
$PythonPath = "C:\Users\antho\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

Stop-Process -Name python -Force -ErrorAction SilentlyContinue

Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vchip_authority_server.py 8020" -RedirectStandardOutput "$EarthDir\auth_out.log" -RedirectStandardError "$EarthDir\auth_err.log" -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vchip_reality_sink.py 8040" -RedirectStandardOutput "$EarthDir\sink_out.log" -RedirectStandardError "$EarthDir\sink_err.log" -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\cappo_unified_engine.py server 8050" -RedirectStandardOutput "$EarthDir\cappo_out.log" -RedirectStandardError "$EarthDir\cappo_err.log" -WindowStyle Hidden
Start-Process -FilePath $PythonPath -ArgumentList "$EarthDir\vfrac_continuum_proof_engine.py server 8060" -RedirectStandardOutput "$EarthDir\cont_out.log" -RedirectStandardError "$EarthDir\cont_err.log" -WindowStyle Hidden
