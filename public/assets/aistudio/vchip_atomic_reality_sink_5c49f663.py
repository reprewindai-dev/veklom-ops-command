#!/usr/bin/env python3
"""
V-Chip Atomic Reality Sink with Write-Ahead Logging & Deterministic Fault Injection
===================================================================================

Architecture:
  - Synchronous Write-Ahead Journaling (WAL) with os.fsync.
  - Fault Barrier Injection (A, B, C) via Win32 TerminateProcess hard-kill.
  - Deterministic Crash Recovery:
      * Barrier A: Crashes before WAL write. Recovery: 0 consequences, retry succeeds.
      * Barrier B: Crashes after consume, before commit. Recovery: Rollback uncommitted, retry succeeds.
      * Barrier C: Crashes after commit, before HTTP ACK. Recovery: Durable commit retained, retry denied.
  - Strict Consequence-Once Invariant:
      For all permits P: #DurableConsequences(P) <= 1
"""

import os
import sys
import json
import time
import ctypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

from vchip_core import (
    ConsequencePermit, verify_signature, ALLOW, DENY_BAD_SIGNATURE, DENY_REPLAYED_OPERATION
)

# Win32 Process Termination (Proper 64-bit handle configuration)
kernel32 = ctypes.windll.kernel32
kernel32.GetCurrentProcess.restype = ctypes.c_void_p
kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAL_FILE = os.path.join(BASE_DIR, "atomic_reality_sink.wal")
BARRIER_FILE = os.path.join(BASE_DIR, "barrier_record.json")
STATE_FILE = os.path.join(BASE_DIR, "atomic_reality_state.json")

LOCK = threading.Lock()
APPLIED_PERMITS = set() # (execution_id, epoch, operation_id)
REALITY_STATE = {
    "counter": 100,
    "applied_operations": []
}
AUTHORITY_PUBLIC_KEY = None

def write_barrier_record(trial_id, fault_window, execution_id, operation_id, permit_digest, epoch, barrier_name):
    record = {
        "trial_id": trial_id,
        "fault_window": fault_window,
        "execution_id": execution_id,
        "operation_id": operation_id,
        "permit_digest": permit_digest,
        "epoch": epoch,
        "process_id": os.getpid(),
        "barrier_name": barrier_name,
        "timestamp": time.time()
    }
    with open(BARRIER_FILE, "w") as f:
        json.dump(record, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    print(f"[!] BARRIER HIT: {barrier_name} for Op {operation_id} (PID {os.getpid()}) -> Hard terminating via TerminateProcess...", flush=True)

def terminate_self(exit_code=42):
    try:
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(), exit_code)
    except Exception:
        pass
    os._exit(exit_code)

def recover_wal():
    global REALITY_STATE, APPLIED_PERMITS
    if not os.path.exists(WAL_FILE):
        return

    print(f"[*] Recovering Reality Sink from WAL: {WAL_FILE}...", flush=True)
    consumed_entries = {}
    committed_entries = {}

    with open(WAL_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                etype = entry.get("type")
                key = (entry["exec_id"], entry["epoch"], entry["op_id"])
                if etype == "RECORD_CONSUME":
                    consumed_entries[key] = entry
                elif etype == "COMMIT_CONSEQUENCE":
                    committed_entries[key] = entry
            except Exception as e:
                print(f"[!] Corrupt WAL entry skipped: {e}", flush=True)

    # Reconcile Transactions
    with LOCK:
        APPLIED_PERMITS.clear()
        REALITY_STATE["applied_operations"].clear()
        base_counter = 100

        for key, commit in committed_entries.items():
            APPLIED_PERMITS.add(key)
            REALITY_STATE["applied_operations"].append({
                "execution_id": commit["exec_id"],
                "epoch": commit["epoch"],
                "operation_id": commit["op_id"],
                "holder_id": commit.get("holder_id", "UNKNOWN")
            })

        REALITY_STATE["counter"] = base_counter + len(APPLIED_PERMITS)

        # Handle uncommitted Window B transactions (Consumed but not committed)
        uncommitted = [k for k in consumed_entries if k not in committed_entries]
        if uncommitted:
            print(f"[!] WAL Recovery: Found {len(uncommitted)} uncommitted transactions. Rolling back to preserve consequence certainty:", flush=True)
            for u in uncommitted:
                print(f"    -> Rolled back uncommitted op: {u[2]} (Permit is retryable)", flush=True)

    print(f"[*] WAL Recovery Complete: Counter={REALITY_STATE['counter']}, Applied Permits={len(APPLIED_PERMITS)}", flush=True)

class AtomicRealitySinkHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        with LOCK:
            if self.path in ("/v1/counter", "/status"):
                self._respond(200, REALITY_STATE)
            elif self.path == "/v1/pid":
                self._respond(200, {"pid": os.getpid(), "alive": True})
            else:
                self._respond(404, {"error": "NOT_FOUND"})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
            action = data.get("action")
        except Exception as e:
            self._respond(400, {"status": "INVALID_JSON_OR_BODY", "error": str(e)})
            return

        if action == "apply_permit":
            permit_dict = data.get("permit")
            if not permit_dict:
                self._respond(400, {"status": "MISSING_PERMIT"})
                return

            permit = ConsequencePermit.from_dict(permit_dict)
            op_key = (permit.execution_id, permit.epoch, permit.operation_id)
            fault_barrier = data.get("fault_barrier")  # "A", "B", or "C"
            trial_id = data.get("trial_id", "TRIAL_UNKNOWN")

            with LOCK:
                # 1. Double-Spend Fencing
                if op_key in APPLIED_PERMITS:
                    print(f"[!] SINK DENIAL [DENY_REPLAYED_OPERATION]: Op {permit.operation_id} already applied!", flush=True)
                    self._respond(400, {"status": DENY_REPLAYED_OPERATION})
                    return

                # 2. Cryptographic Authority Verification
                if AUTHORITY_PUBLIC_KEY and not verify_signature(AUTHORITY_PUBLIC_KEY, permit.authority_signature, permit.canonical_bytes()):
                    self._respond(400, {"status": DENY_BAD_SIGNATURE})
                    return

                # =============================================================
                # FAULT BARRIER A: Validated, but NOT durably consumed
                # =============================================================
                if fault_barrier == "A":
                    write_barrier_record(trial_id, "A", permit.execution_id, permit.operation_id, permit.authority_signature[:16], permit.epoch, "BARRIER_A_REACHED")
                    terminate_self(42)
                    return

                # Write-Ahead Log: RECORD_CONSUME
                wal_entry_consume = {
                    "type": "RECORD_CONSUME",
                    "exec_id": permit.execution_id,
                    "epoch": permit.epoch,
                    "op_id": permit.operation_id,
                    "holder_id": permit.holder_id,
                    "ts": time.time()
                }
                with open(WAL_FILE, "a") as f:
                    f.write(json.dumps(wal_entry_consume) + "\n")
                    f.flush()
                    os.fsync(f.fileno())

                # =============================================================
                # FAULT BARRIER B: Durably marked consumed, but NOT committed
                # =============================================================
                if fault_barrier == "B":
                    write_barrier_record(trial_id, "B", permit.execution_id, permit.operation_id, permit.authority_signature[:16], permit.epoch, "BARRIER_B_REACHED")
                    terminate_self(42)
                    return

                # Commit Consequence to Memory
                APPLIED_PERMITS.add(op_key)
                REALITY_STATE["counter"] += 1
                REALITY_STATE["applied_operations"].append({
                    "execution_id": permit.execution_id,
                    "epoch": permit.epoch,
                    "operation_id": permit.operation_id,
                    "holder_id": permit.holder_id
                })

                # Write-Ahead Log: COMMIT_CONSEQUENCE
                wal_entry_commit = {
                    "type": "COMMIT_CONSEQUENCE",
                    "exec_id": permit.execution_id,
                    "epoch": permit.epoch,
                    "op_id": permit.operation_id,
                    "holder_id": permit.holder_id,
                    "new_counter": REALITY_STATE["counter"],
                    "ts": time.time()
                }
                with open(WAL_FILE, "a") as f:
                    f.write(json.dumps(wal_entry_commit) + "\n")
                    f.flush()
                    os.fsync(f.fileno())

                # Save checkpoint state to JSON
                with open(STATE_FILE, "w") as f:
                    json.dump(REALITY_STATE, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())

                # =============================================================
                # FAULT BARRIER C: Consequence committed, but ACK lost
                # =============================================================
                if fault_barrier == "C":
                    write_barrier_record(trial_id, "C", permit.execution_id, permit.operation_id, permit.authority_signature[:16], permit.epoch, "BARRIER_C_REACHED")
                    terminate_self(42)
                    return

                # Normal Positive ACK
                self._respond(200, {"status": ALLOW, "current_state": REALITY_STATE})

        elif action == "reset_sink":
            with LOCK:
                APPLIED_PERMITS.clear()
                REALITY_STATE["counter"] = 100
                REALITY_STATE["applied_operations"].clear()
                if os.path.exists(WAL_FILE):
                    os.remove(WAL_FILE)
                if os.path.exists(BARRIER_FILE):
                    os.remove(BARRIER_FILE)
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
            self._respond(200, {"status": "SINK_RESET_OK", "counter": 100})

        else:
            self._respond(400, {"status": "INVALID_ACTION"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

def run_atomic_sink(port=8040):
    recover_wal()
    server = ThreadingHTTPServer(("0.0.0.0", port), AtomicRealitySinkHandler)
    print(f"==========================================================", flush=True)
    print(f" V-CHIP ATOMIC REALITY SINK WITH WAL ONLINE (Port {port})", flush=True)
    print(f" Process PID: {os.getpid()}", flush=True)
    print(f" Strict Consequence-Once & Fault Injection Active", flush=True)
    print(f"==========================================================", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8040
    run_atomic_sink(port)
