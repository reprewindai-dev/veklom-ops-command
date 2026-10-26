#!/usr/bin/env python3
"""
Earth Crash Supervisor Daemon
=============================

Runs independently on the enforcing host (Earth or local testbed).
Monitors, terminates, and restarts the Atomic Reality Sink child process.
Exposes control endpoints for the external experiment controller (Mars):
  - GET  /supervisor/status  : Returns victim PID, alive state, barrier record
  - POST /supervisor/restart : Restarts victim after crash, waits for port 8040 readiness
  - POST /supervisor/reset   : Cleans WAL and resets sink to baseline 100
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BARRIER_FILE = os.path.join(BASE_DIR, "barrier_record.json")
WAL_FILE = os.path.join(BASE_DIR, "atomic_reality_sink.wal")
STATE_FILE = os.path.join(BASE_DIR, "atomic_reality_state.json")

VICTIM_SCRIPT = os.path.join(BASE_DIR, "vchip_atomic_reality_sink.py")
VICTIM_PORT = 8040
SUPERVISOR_PORT = 8042

VICTIM_PROC = None
PREVIOUS_PID = None

def spawn_victim():
    global VICTIM_PROC, PREVIOUS_PID
    if VICTIM_PROC and VICTIM_PROC.poll() is None:
        return VICTIM_PROC.pid

    py_exe = sys.executable
    cmd = [py_exe, VICTIM_SCRIPT, str(VICTIM_PORT)]
    print(f"[*] Supervisor spawning Atomic Reality Sink on port {VICTIM_PORT}...", flush=True)
    
    VICTIM_PROC = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    new_pid = VICTIM_PROC.pid
    print(f"[+] Spawned Victim Process PID: {new_pid}", flush=True)
    
    # Wait for sink to respond on port 8040
    ready = False
    for _ in range(30):
        time.sleep(0.1)
        try:
            url = f"http://127.0.0.1:{VICTIM_PORT}/v1/pid"
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass
    if ready:
        print(f"[+] Victim Process PID {new_pid} is confirmed listening on port {VICTIM_PORT}", flush=True)
    else:
        print(f"[!] Warning: Victim Process PID {new_pid} did not respond within timeout", flush=True)
    return new_pid

class SupervisorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global VICTIM_PROC, PREVIOUS_PID
        if self.path == "/supervisor/status":
            if VICTIM_PROC is not None:
                VICTIM_PROC.poll()
            alive = VICTIM_PROC is not None and VICTIM_PROC.poll() is None
            exit_code = VICTIM_PROC.poll() if VICTIM_PROC else None
            curr_pid = VICTIM_PROC.pid if VICTIM_PROC else None

            barrier_data = None
            if os.path.exists(BARRIER_FILE):
                try:
                    with open(BARRIER_FILE, "r") as f:
                        barrier_data = json.load(f)
                except Exception:
                    pass

            resp = {
                "supervisor_status": "ONLINE",
                "victim_pid": curr_pid,
                "victim_alive": alive,
                "exit_code": exit_code,
                "previous_pid": PREVIOUS_PID,
                "barrier_record": barrier_data
            }
            self._respond(200, resp)
        else:
            self._respond(404, {"error": "UNKNOWN_ENDPOINT"})

    def do_POST(self):
        global VICTIM_PROC, PREVIOUS_PID
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}
        action = data.get("action", self.path.strip("/").split("/")[-1])

        if action == "restart":
            old_pid = VICTIM_PROC.pid if VICTIM_PROC else None
            if VICTIM_PROC and VICTIM_PROC.poll() is None:
                # Force kill if still alive
                import ctypes
                ctypes.windll.kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
                ctypes.windll.kernel32.TerminateProcess(int(VICTIM_PROC._handle), 42)
                VICTIM_PROC.wait(timeout=2)
            
            PREVIOUS_PID = old_pid
            new_pid = spawn_victim()
            self._respond(200, {
                "status": "RESTARTED",
                "previous_pid": old_pid,
                "new_pid": new_pid
            })

        elif action == "reset":
            if VICTIM_PROC and VICTIM_PROC.poll() is None:
                import ctypes
                ctypes.windll.kernel32.TerminateProcess(int(VICTIM_PROC._handle), 42)
                VICTIM_PROC.wait(timeout=2)

            for f_path in (WAL_FILE, BARRIER_FILE, STATE_FILE):
                if os.path.exists(f_path):
                    try:
                        os.remove(f_path)
                    except Exception:
                        pass

            new_pid = spawn_victim()
            self._respond(200, {
                "status": "RESET_COMPLETE",
                "new_pid": new_pid
            })

        else:
            self._respond(400, {"status": "INVALID_ACTION"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

def run_supervisor(port=SUPERVISOR_PORT):
    spawn_victim()
    server = ThreadingHTTPServer(("0.0.0.0", port), SupervisorHandler)
    print(f"==========================================================", flush=True)
    print(f" EARTH CRASH SUPERVISOR DAEMON ONLINE (Port {port})", flush=True)
    print(f" Supervising Atomic Reality Sink on Port {VICTIM_PORT}", flush=True)
    print(f"==========================================================", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else SUPERVISOR_PORT
    run_supervisor(p)
