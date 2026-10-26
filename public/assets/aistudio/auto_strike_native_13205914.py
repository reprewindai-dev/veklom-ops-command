import socket, time, sys, subprocess
def wait_for_mars():
    print("[*] Polling Mars Gate natively (192.168.2.28:8020) for life...")
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(('192.168.2.28', 8020))
            s.close()
            print("[OK] MARS GATE ONLINE. UNLEASHING 10,000-CHUNK STRIKE.")
            subprocess.run(["C:\\Users\\antho\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe", "-u", "C:\\Users\\antho\\vchip\\vfrac_traversal_strike.py", "http://192.168.2.28:8020", "http://192.168.2.28:8040", "100000"])
            break
        except Exception:
            time.sleep(2)

wait_for_mars()
