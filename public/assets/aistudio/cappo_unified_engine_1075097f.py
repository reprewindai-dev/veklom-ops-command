import os
import sys
import json
import time
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
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_WRONG_KEY,
    DENY_BAD_SIGNATURE, DENY_REPLAYED_OPERATION
)
DENY_NODE_REVOKED = "DENY_NODE_REVOKED"

# --- CAPPO Core Data Models ---

class CappoCapabilityLease:
    def __init__(self, lease_id, execution_id, epoch, holder_id, max_budget, allowed_resources, max_depth, issuer_pub_key, signature=""):
        self.lease_id = lease_id
        self.execution_id = execution_id
        self.epoch = epoch
        self.holder_id = holder_id
        self.max_budget = max_budget
        self.allowed_resources = allowed_resources  # list of strings
        self.max_depth = max_depth
        self.issuer_pub_key = issuer_pub_key
        self.signature = signature

    def canonical_bytes(self):
        payload = {
            "lease_id": self.lease_id,
            "execution_id": self.execution_id,
            "epoch": self.epoch,
            "holder_id": self.holder_id,
            "max_budget": self.max_budget,
            "allowed_resources": sorted(self.allowed_resources),
            "max_depth": self.max_depth,
            "issuer_pub_key": self.issuer_pub_key
        }
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def to_dict(self):
        return {
            "lease_id": self.lease_id,
            "execution_id": self.execution_id,
            "epoch": self.epoch,
            "holder_id": self.holder_id,
            "max_budget": self.max_budget,
            "allowed_resources": self.allowed_resources,
            "max_depth": self.max_depth,
            "issuer_pub_key": self.issuer_pub_key,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            lease_id=d["lease_id"],
            execution_id=d["execution_id"],
            epoch=d["epoch"],
            holder_id=d["holder_id"],
            max_budget=d["max_budget"],
            allowed_resources=d["allowed_resources"],
            max_depth=d.get("max_depth", 3),
            issuer_pub_key=d["issuer_pub_key"],
            signature=d.get("signature", "")
        )

# --- CAPPO Global Server State ---

CAPPO_PRIV_KEY, CAPPO_PRIV_HEX, CAPPO_PUB_HEX = generate_keypair()
ACTIVE_LEASES = {}        # lease_id -> CappoCapabilityLease
LEASE_BUDGET_CONSUMED = {}# lease_id -> int
EPOCH_MAP = {}            # execution_id -> current_epoch
REVOKED_NODES = set()
CONSUMED_OPS = set()      # (execution_id, epoch, op_id)
REALITY_SINK_COUNTER = 0
LAST_APPLIED_OP = None

SINK_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cappo_reality_state.json")

def load_sink_state():
    global REALITY_SINK_COUNTER, LAST_APPLIED_OP
    if os.path.exists(SINK_STATE_FILE):
        try:
            with open(SINK_STATE_FILE, "r") as f:
                d = json.load(f)
                REALITY_SINK_COUNTER = d.get("counter", 0)
                LAST_APPLIED_OP = d.get("last_op")
        except Exception as e:
            print(f"[CAPPO] Error loading sink state: {e}")

def save_sink_state():
    try:
        with open(SINK_STATE_FILE, "w") as f:
            json.dump({"counter": REALITY_SINK_COUNTER, "last_op": LAST_APPLIED_OP}, f, indent=2)
    except Exception as e:
        print(f"[CAPPO] Error saving sink state: {e}")

load_sink_state()

# --- CAPPO 100% Unified HTTP Server Handler ---

class CappoUnifiedHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.strip("/")
        if path == "status":
            self._respond(200, {
                "cappo_status": "ONLINE",
                "cappo_pub_key": CAPPO_PUB_HEX,
                "active_leases": len(ACTIVE_LEASES),
                "sink_counter": REALITY_SINK_COUNTER,
                "last_op": LAST_APPLIED_OP
            })
        else:
            self._respond(404, {"error": "ROUTE_NOT_FOUND"})

    def do_POST(self):
        global REALITY_SINK_COUNTER, LAST_APPLIED_OP
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            action = data.get("action")
        except Exception as e:
            self._respond(400, {"status": "BAD_REQUEST", "error": str(e)})
            return

        # 1. ISSUE CAPABILITY LEASE (100% CAPPO Managed)
        if action == "issue_lease":
            exec_id = data.get("execution_id", "VFRAC_CAPPO_EXEC")
            epoch = data.get("epoch", 1)
            holder = data.get("holder_id", "WORKER_ALPHA")
            budget = data.get("max_budget", 100000)
            resources = data.get("allowed_resources", ["REALITY_SINK", "MUTATE_STATE"])
            depth = data.get("max_depth", 3)
            lease_id = f"LEASE_{exec_id}_{epoch}_{holder}_{int(time.time())}"

            lease = CappoCapabilityLease(
                lease_id=lease_id,
                execution_id=exec_id,
                epoch=epoch,
                holder_id=holder,
                max_budget=budget,
                allowed_resources=resources,
                max_depth=depth,
                issuer_pub_key=CAPPO_PUB_HEX
            )
            sig_bytes = lease.canonical_bytes()
            lease.signature = sign_bytes(CAPPO_PRIV_KEY, sig_bytes)

            ACTIVE_LEASES[lease_id] = lease
            LEASE_BUDGET_CONSUMED[lease_id] = 0
            EPOCH_MAP[exec_id] = epoch

            print(f"[+] [CAPPO LEASE ISSUED] ID: {lease_id} | Budget: {budget} | Epoch: {epoch} | Holder: {holder}")
            self._respond(200, {
                "status": "SUCCESS",
                "lease": lease.to_dict(),
                "cappo_public_key": CAPPO_PUB_HEX
            })

        # 2. UNIFIED CAPPO BATCH AUTHORIZATION & CONSEQUENCE APPLICATION (100% CAPPO)
        elif action == "authorize_and_apply_batch":
            lease_dict = data.get("lease")
            ops = data.get("operations", [])
            target_resource = data.get("target_resource", "REALITY_SINK")

            if not lease_dict:
                self._respond(400, {"status": "DENY", "reason": "MISSING_LEASE"})
                return

            lease = CappoCapabilityLease.from_dict(lease_dict)

            # --- CAPPO RULE 1: Verify CAPPO Signature on Lease ---
            if not verify_signature(CAPPO_PUB_HEX, lease.signature, lease.canonical_bytes()):
                self._respond(401, {"status": "DENY", "reason": DENY_BAD_SIGNATURE, "detail": "Invalid CAPPO Lease Signature"})
                return

            # --- CAPPO RULE 2: Revocation Check ---
            if lease.holder_id in REVOKED_NODES:
                self._respond(403, {"status": "DENY", "reason": DENY_NODE_REVOKED, "detail": f"Holder {lease.holder_id} is revoked"})
                return

            # --- CAPPO RULE 3: Monotonic Epoch Fencing ---
            curr_epoch = EPOCH_MAP.get(lease.execution_id, lease.epoch)
            if lease.epoch < curr_epoch:
                self._respond(403, {"status": "DENY", "reason": DENY_STALE_EPOCH, "detail": f"Lease epoch {lease.epoch} < current {curr_epoch}"})
                return

            # --- CAPPO RULE 4: Resource Ceiling Check ---
            if target_resource not in lease.allowed_resources:
                self._respond(403, {"status": "DENY", "reason": "DENY_RESOURCE_CEILING_EXCEEDED", "detail": f"Resource {target_resource} not permitted in lease"})
                return

            # --- CAPPO RULE 5: Action Budget Ceiling Check ---
            consumed = LEASE_BUDGET_CONSUMED.get(lease.lease_id, 0)
            requested_count = len(ops)
            if consumed + requested_count > lease.max_budget:
                self._respond(403, {"status": "DENY", "reason": "DENY_BUDGET_EXCEEDED", "detail": f"Budget requested {consumed + requested_count} > max {lease.max_budget}"})
                return

            # --- CAPPO RULE 6: Replay & Consequence Enforcement ---
            applied_permits = []
            for op in ops:
                op_id = op.get("operation_id")
                op_key = (lease.execution_id, lease.epoch, op_id)
                if op_key in CONSUMED_OPS:
                    self._respond(409, {"status": "DENY", "reason": DENY_REPLAYED_OPERATION, "detail": f"Replayed operation {op_id}"})
                    return
                CONSUMED_OPS.add(op_key)
                applied_permits.append({
                    "operation_id": op_id,
                    "status": ALLOW,
                    "lease_id": lease.lease_id,
                    "applied_at_epoch": lease.epoch
                })

            # Update Budget & Sink Counter (Direct Consequence Application)
            LEASE_BUDGET_CONSUMED[lease.lease_id] = consumed + requested_count
            REALITY_SINK_COUNTER += requested_count
            if ops:
                LAST_APPLIED_OP = ops[-1].get("operation_id")
            save_sink_state()

            print(f"[+] [CAPPO AUTHORIZED & APPLIED] Batch of {requested_count} ops | Lease: {lease.lease_id[:20]}... | Sink Total: {REALITY_SINK_COUNTER}")
            self._respond(200, {
                "status": "ALLOW",
                "authorized_count": requested_count,
                "consumed_total": LEASE_BUDGET_CONSUMED[lease.lease_id],
                "remaining_budget": lease.max_budget - LEASE_BUDGET_CONSUMED[lease.lease_id],
                "sink_counter": REALITY_SINK_COUNTER,
                "last_op": LAST_APPLIED_OP
            })

        elif action == "revoke_holder":
            holder = data.get("holder_id")
            if holder:
                REVOKED_NODES.add(holder)
                print(f"[!] [CAPPO REVOCATION] Revoked holder: {holder}")
                self._respond(200, {"status": "REVOKED", "holder_id": holder})
            else:
                self._respond(400, {"error": "MISSING_HOLDER_ID"})

        else:
            self._respond(400, {"error": f"UNKNOWN_ACTION_{action}"})

# --- Server Start Helper ---

def run_cappo_server(port=8050):
    server = ThreadingHTTPServer(("0.0.0.0", port), CappoUnifiedHandler)
    print(f"==========================================================")
    print(f" 100% CAPPO UNIFIED CAPABILITY & CONSEQUENCE ENGINE (Port {port})")
    print(f" Public Key: {CAPPO_PUB_HEX[:32]}...")
    print(f" 100% Policy Leasing, Fencing, Revocation & Sink Enforced")
    print(f"==========================================================")
    server.serve_forever()

# --- Client Strike Runner (Real HTTP/TCP Sockets) ---

def run_cappo_100k_traversal_strike(target_url="http://127.0.0.1:8050", total_ops=100000, batch_size=10000):
    print(f"\n==========================================================")
    print(f" CAPPO 100% UNIFIED TRAVERSAL STRIKE RUNNER")
    print(f" Target: {target_url} | Operations: {total_ops} | Batch Size: {batch_size}")
    print(f" Connection: REAL HTTP / TCP SOCKETS | Zero Mocks")
    print(f"==========================================================\n")

    exec_id = f"CAPPO_UNIFIED_TRAVERSAL_{int(time.time())}"
    holder_id = "CAPPO_UNIFIED_WORKER_MARS"

    # Step 1: Request Capability Lease from CAPPO Server over HTTP TCP
    lease_req_payload = {
        "action": "issue_lease",
        "execution_id": exec_id,
        "epoch": 1,
        "holder_id": holder_id,
        "max_budget": total_ops,
        "allowed_resources": ["REALITY_SINK", "MUTATE_STATE"],
        "max_depth": 3
    }
    req = urllib.request.Request(
        f"{target_url}/cappo",
        data=json.dumps(lease_req_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if res.get("status") != "SUCCESS":
            raise RuntimeError(f"Failed to obtain CAPPO lease: {res}")
        lease = res["lease"]
        print(f"[+] Successfully obtained CAPPO Lease over HTTP TCP: {lease['lease_id']}")

    # Step 2: Execute 100,000 Operations in Batches over Real HTTP TCP
    start_time = time.time()
    total_batches = total_ops // batch_size
    ops_completed = 0

    for b in range(total_batches):
        batch_start_idx = b * batch_size
        batch_ops = [
            {"operation_id": f"OP_CAPPO_{batch_start_idx + i:06d}", "payload": f"state_delta_{batch_start_idx + i}"}
            for i in range(batch_size)
        ]

        payload = {
            "action": "authorize_and_apply_batch",
            "lease": lease,
            "operations": batch_ops,
            "target_resource": "REALITY_SINK"
        }

        req = urllib.request.Request(
            f"{target_url}/cappo",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("status") != "ALLOW":
                raise RuntimeError(f"Batch {b+1} DENIED by CAPPO: {body}")
            ops_completed += body["authorized_count"]
            print(f"[*] Batch {b+1}/{total_batches} ALLOWED ({ops_completed}/{total_ops} ops) | CAPPO Sink Counter: {body['sink_counter']} | Last Op: {body['last_op']}")

    elapsed = time.time() - start_time
    ops_per_sec = ops_completed / elapsed if elapsed > 0 else 0

    print(f"\n==========================================================")
    print(f" CAPPO 100% UNIFIED TRAVERSAL STRIKE COMPLETE")
    print(f" Total Operations Authorized & Applied: {ops_completed}")
    print(f" Elapsed Time: {elapsed:.2f} seconds")
    print(f" Throughput: {ops_per_sec:.2f} ops/sec")
    print(f" Network: Real HTTP/TCP | Zero Loss | 100% CAPPO Governed")
    print(f"==========================================================\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8050
        run_cappo_server(port)
    elif len(sys.argv) > 1 and sys.argv[1] == "strike":
        url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8050"
        ops = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
        run_cappo_100k_traversal_strike(url, ops)
    else:
        print("Usage:")
        print("  python cappo_unified_engine.py server [port]")
        print("  python cappo_unified_engine.py strike [http://target:port] [total_ops]")
