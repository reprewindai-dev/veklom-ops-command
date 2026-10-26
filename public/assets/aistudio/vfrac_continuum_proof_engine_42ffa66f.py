import os
import sys
import json
import time
import hashlib
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

from vchip_core import (
    generate_keypair, sign_bytes, verify_signature,
    ALLOW, DENY_STALE_EPOCH
)
DENY_NODE_REVOKED = "DENY_NODE_REVOKED"

# --- Cryptographic Ledger Helpers (GnomLedger DAG) ---

def compute_node_hash(prev_hash, node_type, lineage_id, epoch, payload):
    data = f"{prev_hash}|{node_type}|{lineage_id}|{epoch}|{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

# --- CONTINUUM PROOF ENGINE SERVER ---

SERVER_PRIV_KEY, SERVER_PRIV_HEX, SERVER_PUB_HEX = generate_keypair()

STATE_STORE = {
    "epochs": {"L1_PRIMARY": 1},
    "revoked_holders": set(),
    "ledger_dag": [], # list of H_n entries
    "reality_sink": {"counter": 0, "last_op": None, "state_hash": "GENESIS_HASH"},
    "tarpit_log": []
}

class ContinuumServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            action = data.get("action")
        except Exception as e:
            self._respond(400, {"status": "ERROR", "message": str(e)})
            return

        # -----------------------------------------------------------------
        # PROOF 1: GHOST WORKLOAD ADVERSARIAL TARPIT
        # -----------------------------------------------------------------
        if action == "execute_with_tarpit_check":
            holder = data.get("holder_id")
            epoch = data.get("epoch", 1)
            lineage_id = data.get("lineage_id", "L1_PRIMARY")
            ops = data.get("operations", [])

            curr_epoch = STATE_STORE["epochs"].get(lineage_id, 1)

            # Check if holder is revoked or running stale epoch
            is_revoked = holder in STATE_STORE["revoked_holders"]
            is_stale = epoch < curr_epoch

            if is_revoked or is_stale:
                # ROUTE TO GHOST TARPIT VOID (Simulated Success for Attacker, 0 Real State Mutation)
                tarpit_entry = {
                    "timestamp": time.time(),
                    "holder_id": holder,
                    "rejected_reason": "REVOKED" if is_revoked else "STALE_EPOCH",
                    "fake_permits_issued": len(ops)
                }
                STATE_STORE["tarpit_log"].append(tarpit_entry)
                self._respond(200, {
                    "status": "ALLOW_TARPIT_VOID",
                    "tarpit_active": True,
                    "message": "Consequences routed to phantom sink",
                    "fake_applied_count": len(ops),
                    "real_state_mutation": False
                })
                return

            # Real Consequence Path
            prev_hash = STATE_STORE["reality_sink"]["state_hash"]
            new_hash = compute_node_hash(prev_hash, "SINK_MUTATION", lineage_id, epoch, ops)
            
            STATE_STORE["reality_sink"]["counter"] += len(ops)
            if ops:
                STATE_STORE["reality_sink"]["last_op"] = ops[-1].get("op_id")
            STATE_STORE["reality_sink"]["state_hash"] = new_hash
            STATE_STORE["ledger_dag"].append({"hash": new_hash, "ops": len(ops), "lineage": lineage_id})

            self._respond(200, {
                "status": "ALLOW_REAL_SINK",
                "tarpit_active": False,
                "real_applied_count": len(ops),
                "sink_counter": STATE_STORE["reality_sink"]["counter"],
                "state_hash": new_hash
            })

        elif action == "advance_epoch":
            lineage_id = data.get("lineage_id", "L1_PRIMARY")
            new_epoch = data.get("new_epoch", 2)
            revoke_holder = data.get("revoke_holder")
            STATE_STORE["epochs"][lineage_id] = new_epoch
            if revoke_holder:
                STATE_STORE["revoked_holders"].add(revoke_holder)
            self._respond(200, {"status": "EPOCH_ADVANCED", "lineage_id": lineage_id, "epoch": new_epoch})

        # -----------------------------------------------------------------
        # PROOF 2: SPATIO-TEMPORAL WORKLOAD FRACTURING
        # -----------------------------------------------------------------
        elif action == "apply_fracture_chunk":
            fracture_id = data.get("fracture_id")
            lineage_id = data.get("lineage_id")
            ops_count = data.get("ops_count", 0)
            partial_hash = data.get("partial_hash")

            prev_hash = STATE_STORE["reality_sink"]["state_hash"]
            combined_hash = hashlib.sha256(f"{prev_hash}:{fracture_id}:{partial_hash}".encode()).hexdigest()

            STATE_STORE["reality_sink"]["counter"] += ops_count
            STATE_STORE["reality_sink"]["state_hash"] = combined_hash
            STATE_STORE["ledger_dag"].append({
                "hash": combined_hash,
                "fracture_id": fracture_id,
                "ops": ops_count
            })

            self._respond(200, {
                "status": "FRACTURE_ASSEMBLED",
                "fracture_id": fracture_id,
                "ops_applied": ops_count,
                "total_counter": STATE_STORE["reality_sink"]["counter"],
                "combined_hash": combined_hash
            })

        # -----------------------------------------------------------------
        # PROOF 3: TIME-TRAVEL STATE FORKING
        # -----------------------------------------------------------------
        elif action == "fork_timeline":
            source_lineage = data.get("source_lineage")
            fork_at_hash = data.get("fork_at_hash")
            new_lineage = data.get("new_lineage")

            STATE_STORE["epochs"][new_lineage] = 1
            STATE_STORE["ledger_dag"].append({
                "hash": f"FORK_GENESIS_{new_lineage}",
                "forked_from": fork_at_hash,
                "lineage": new_lineage
            })
            self._respond(200, {
                "status": "TIMELINE_FORKED",
                "new_lineage": new_lineage,
                "fork_root": fork_at_hash
            })

        # -----------------------------------------------------------------
        # PROOF 4: INSIDER THREAT TAMPER AUDIT
        # -----------------------------------------------------------------
        elif action == "audit_disk_integrity":
            disk_counter = data.get("disk_counter")
            disk_hash = data.get("disk_hash")

            real_counter = STATE_STORE["reality_sink"]["counter"]
            real_hash = STATE_STORE["reality_sink"]["state_hash"]

            if disk_counter != real_counter or disk_hash != real_hash:
                self._respond(403, {
                    "status": "INSIDER_TAMPERING_DETECTED",
                    "tamper_alert": True,
                    "disk_state": {"counter": disk_counter, "hash": disk_hash},
                    "ledger_state": {"counter": real_counter, "hash": real_hash},
                    "action_taken": "ISOLATE_NODE_AND_ROUTE_AROUND"
                })
            else:
                self._respond(200, {"status": "INTEGRITY_VERIFIED", "tamper_alert": False})

        else:
            self._respond(400, {"error": "UNKNOWN_ACTION"})

def run_server(port=8060):
    server = ThreadingHTTPServer(("0.0.0.0", port), ContinuumServerHandler)
    print(f"[+] CONTINUUM PROOF SERVER ONLINE on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server(int(sys.argv[2]) if len(sys.argv) > 2 else 8060)
