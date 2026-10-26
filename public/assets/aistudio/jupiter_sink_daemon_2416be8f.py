import os
import sys
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

for p in [r"C:\Users\antho\scratch\pylibs", r"C:\Users\antho\vchip", os.path.dirname(os.path.abspath(__file__))]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from vchip_core import verify_signature, ALLOW, DENY_BAD_SIGNATURE, DENY_REPLAYED_OPERATION
except ImportError:
    verify_signature = None
    ALLOW = "ALLOW"
    DENY_BAD_SIGNATURE = "DENY_BAD_SIGNATURE"
    DENY_REPLAYED_OPERATION = "DENY_REPLAYED_OPERATION"

REALITY_STATE = {
    "counter": 0,
    "applied_operations": []
}
APPLIED_PERMITS = set()
LOCK = threading.Lock()
AUTHORITY_PUBLIC_KEY = None

class RealitySinkHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        with LOCK:
            self._respond(200, REALITY_STATE)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_body)
            action = data.get("action")
        except Exception as e:
            self._respond(400, {"status": "INVALID_JSON_OR_BODY", "error": str(e)})
            return

        if action == "apply_permit":
            permit = data.get("permit", {})
            if not permit:
                self._respond(400, {"status": "MISSING_PERMIT"})
                return

            exec_id = permit.get("execution_id", "UNKNOWN")
            epoch = permit.get("epoch", 0)
            op_id = permit.get("operation_id", "")
            holder = permit.get("holder_id", "")
            sig = permit.get("authority_signature", "")
            op_key = (exec_id, epoch, op_id)

            with LOCK:
                if op_key in APPLIED_PERMITS:
                    print(f"[!] REALITY SINK DENIAL: Replayed op {op_id}", flush=True)
                    self._respond(400, {"status": DENY_REPLAYED_OPERATION})
                    return

                if AUTHORITY_PUBLIC_KEY and verify_signature:
                    canonical_dict = {
                        "execution_id": exec_id,
                        "epoch": epoch,
                        "holder_id": holder,
                        "operation_id": op_id,
                        "state_root": permit.get("state_root", ""),
                        "evidence_head": permit.get("evidence_head", "")
                    }
                    canonical_bytes = json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
                    if not verify_signature(AUTHORITY_PUBLIC_KEY, sig, canonical_bytes):
                        print(f"[!] REALITY SINK DENIAL: Invalid permit signature", flush=True)
                        self._respond(400, {"status": DENY_BAD_SIGNATURE})
                        return

                APPLIED_PERMITS.add(op_key)
                REALITY_STATE["counter"] += 1
                REALITY_STATE["applied_operations"].append({
                    "execution_id": exec_id,
                    "epoch": epoch,
                    "operation_id": op_id,
                    "holder_id": holder
                })

                state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reality_state.json")
                try:
                    with open(state_file, "w") as f:
                        json.dump(REALITY_STATE, f, indent=2)
                except Exception:
                    pass

                print(f"[+] REALITY SINK APPLIED PERMIT: Op {op_id} | Counter: {REALITY_STATE['counter']}", flush=True)
                self._respond(200, {"status": ALLOW, "current_state": REALITY_STATE})

        elif action == "reset_sink":
            with LOCK:
                REALITY_STATE["counter"] = 0
                REALITY_STATE["applied_operations"].clear()
                APPLIED_PERMITS.clear()
            self._respond(200, {"status": "RESET", "counter": 0})

        else:
            self._respond(400, {"status": "INVALID_ACTION"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8040
    server = ThreadingHTTPServer(("0.0.0.0", port), RealitySinkHandler)
    print(f"[*] Jupiter Reality Sink online at 0.0.0.0:{port} (Initial Counter: 0)", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()
