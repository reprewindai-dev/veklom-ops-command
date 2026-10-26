import os
import sys
import json
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

# Global State for Independent Reality Sink
APPLIED_PERMITS = set() # (execution_id, epoch, operation_id)
REALITY_STATE = {
    "counter": 100,
    "applied_operations": []
}
LOCK = threading.Lock()
AUTHORITY_PUBLIC_KEY = None

class RealitySinkHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        with LOCK:
            self._respond(200, REALITY_STATE)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)

        action = data.get("action")
        if action == "apply_permit":
            permit_dict = data.get("permit")
            if not permit_dict:
                self._respond(400, {"status": "MISSING_PERMIT"})
                return

            permit = ConsequencePermit.from_dict(permit_dict)
            op_key = (permit.execution_id, permit.epoch, permit.operation_id)

            with LOCK:
                # 1. Double-Spend Fencing
                if op_key in APPLIED_PERMITS:
                    print(f"[!] REALITY SINK DENIAL [DENY_REPLAYED_OPERATION]: Op {permit.operation_id} already applied!")
                    self._respond(400, {"status": DENY_REPLAYED_OPERATION})
                    return

                # 2. Cryptographic Authority Signature Verification
                if AUTHORITY_PUBLIC_KEY and not verify_signature(AUTHORITY_PUBLIC_KEY, permit.authority_signature, permit.canonical_bytes()):
                    print(f"[!] REALITY SINK DENIAL [DENY_BAD_SIGNATURE]: Permit signature verification failed!")
                    self._respond(400, {"status": DENY_BAD_SIGNATURE})
                    return

                # ALLOW! Apply Physical Consequence
                APPLIED_PERMITS.add(op_key)
                REALITY_STATE["counter"] += 1
                REALITY_STATE["applied_operations"].append({
                    "execution_id": permit.execution_id,
                    "epoch": permit.epoch,
                    "operation_id": permit.operation_id,
                    "holder_id": permit.holder_id
                })

                # Write state to file
                state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reality_state.json")
                with open(state_file, "w") as f:
                    json.dump(REALITY_STATE, f, indent=2)

                print(f"[+] REALITY SINK APPLIED PERMIT: Op {permit.operation_id} | Counter: {REALITY_STATE['counter']}")
                self._respond(200, {"status": ALLOW, "current_state": REALITY_STATE})
        else:
            self._respond(400, {"status": "INVALID_ACTION"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

def run_sink(pubkey=None, port=8040):
    global AUTHORITY_PUBLIC_KEY
    AUTHORITY_PUBLIC_KEY = pubkey

    server = ThreadingHTTPServer(("0.0.0.0", port), RealitySinkHandler)
    print("==========================================================")
    print(f" V-CHIP INDEPENDENT REALITY SINK ONLINE (Port {port})")
    print(f" Authority Public Key Filter: {AUTHORITY_PUBLIC_KEY[:16] if AUTHORITY_PUBLIC_KEY else 'NONE (WARNING)'}...")
    print("==========================================================")
    server.serve_forever()

if __name__ == "__main__":
    pubkey = sys.argv[1] if len(sys.argv) > 1 and len(sys.argv[1]) > 10 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else (int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8040)
    run_sink(pubkey, port)
