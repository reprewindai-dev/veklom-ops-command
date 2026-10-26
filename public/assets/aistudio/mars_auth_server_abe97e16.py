import os
import sys
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

from vchip_core import (
    AuthorityRecord, HandoffPackage, ConsequenceRequest, ConsequencePermit,
    generate_keypair, sign_bytes, verify_signature,
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_WRONG_KEY,
    DENY_BAD_SIGNATURE, DENY_WRONG_EXECUTION, DENY_REPLAYED_OPERATION,
    DENY_STATE_MISMATCH
)
from vfrac_recursive_core import DelegationCertificate, RecursiveConsequenceRequest

# Global State
AUTHORITY_STORE = {}
CONSUMED_OPERATIONS = set() # (execution_id, epoch, operation_id)
REVOKED_NODES = set()       # set of revoked node_ids
NODE_CEILINGS = {}          # node_id -> set of allowed resources
AUTH_SIGNING_KEY, AUTH_PRIV_HEX, AUTH_PUB_HEX = generate_keypair()

class DecoupledAuthorityHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = self.path.strip("/")
        if path in AUTHORITY_STORE:
            rec = AUTHORITY_STORE[path]
            self._respond(200, rec.to_dict())
        else:
            self._respond(404, {"error": "EXECUTION_NOT_FOUND"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)
        action = data.get("action")

        if action in ("register_genesis", "register"):
            if "authority_record" in data:
                rec = AuthorityRecord.from_dict(data["authority_record"])
            else:
                exec_id = data.get("execution_id", "DEFAULT")
                epoch = data.get("epoch", 1)
                holder = data.get("holder") or data.get("holder_id") or "EARTH"
                pub_key = data.get("pub_key") or data.get("authority_public_key", "")
                rec = AuthorityRecord(
                    execution_id=exec_id,
                    current_epoch=epoch,
                    current_holder=holder,
                    authority_public_key=pub_key,
                    previous_evidence_head="GENESIS"
                )
            AUTHORITY_STORE[rec.execution_id] = rec
            print(f"[*] Genesis Registered ({action}): {rec.execution_id} | Epoch {rec.current_epoch} | Holder: {rec.current_holder} | Key: {rec.authority_public_key[:16]}...")
            self._respond(200, {"status": "SUCCESS", "epoch": rec.current_epoch, "authority_service_key": AUTH_PUB_HEX})

        elif action == "handoff":
            pkg = HandoffPackage.from_dict(data["handoff_package"])
            current_rec = AUTHORITY_STORE.get(pkg.execution_id)
            if not current_rec:
                self._respond(400, {"status": "DENY_EXECUTION_NOT_FOUND"})
                return

            # Verify handoff checks
            if pkg.execution_id != current_rec.execution_id:
                self._respond(400, {"status": DENY_WRONG_EXECUTION})
                return
            if pkg.from_epoch != current_rec.current_epoch:
                self._respond(400, {"status": DENY_STALE_EPOCH})
                return
            if pkg.from_holder != current_rec.current_holder:
                self._respond(400, {"status": DENY_WRONG_HOLDER})
                return
            if pkg.to_epoch != pkg.from_epoch + 1:
                self._respond(400, {"status": DENY_STALE_EPOCH})
                return

            # Verify signature with current_rec.authority_public_key
            if not verify_signature(current_rec.authority_public_key, pkg.signature, pkg.canonical_bytes()):
                self._respond(400, {"status": DENY_BAD_SIGNATURE})
                return

            # Handoff Accepted -> Advance Authority Truth
            new_rec = AuthorityRecord(
                execution_id=pkg.execution_id,
                current_epoch=pkg.to_epoch,
                current_holder=pkg.to_holder,
                authority_public_key=pkg.next_public_key,
                previous_evidence_head=pkg.evidence_head
            )
            AUTHORITY_STORE[pkg.execution_id] = new_rec
            print(f"[+] HANDOFF COMMITTED: {pkg.execution_id} | Epoch {pkg.from_epoch} ({pkg.from_holder}) -> Epoch {pkg.to_epoch} ({pkg.to_holder}) | New Key: {pkg.next_public_key[:16]}...")
            self._respond(200, {"status": ALLOW, "new_epoch": pkg.to_epoch})

        elif action == "validate_consequence":
            req = ConsequenceRequest.from_dict(data["request"])
            current_rec = AUTHORITY_STORE.get(req.execution_id)
            if not current_rec:
                self._respond(400, {"status": "DENY_EXECUTION_NOT_FOUND"})
                return

            # 1. Execution ID
            if req.execution_id != current_rec.execution_id:
                self._respond(400, {"status": DENY_WRONG_EXECUTION})
                return

            # 2. Epoch Fencing
            if req.epoch != current_rec.current_epoch:
                print(f"[!] GATE DENIAL [DENY_STALE_EPOCH]: Request Epoch {req.epoch} != Authority Epoch {current_rec.current_epoch}")
                self._respond(400, {"status": DENY_STALE_EPOCH, "current_epoch": current_rec.current_epoch, "current_holder": current_rec.current_holder})
                return

            # 3. Holder Fencing
            if req.holder_id != current_rec.current_holder:
                print(f"[!] GATE DENIAL [DENY_WRONG_HOLDER]: Request Holder {req.holder_id} != Authority Holder {current_rec.current_holder}")
                self._respond(400, {"status": DENY_WRONG_HOLDER})
                return

            # 4. Key Fencing
            if req.signing_key_public != current_rec.authority_public_key:
                print(f"[!] GATE DENIAL [DENY_WRONG_KEY]: Request Key {req.signing_key_public[:16]} != Authority Key {current_rec.authority_public_key[:16]}")
                self._respond(400, {"status": DENY_WRONG_KEY})
                return

            # 5. Replay Fencing
            op_key = (req.execution_id, req.epoch, req.operation_id)
            if op_key in CONSUMED_OPERATIONS:
                print(f"[!] GATE DENIAL [DENY_REPLAYED_OPERATION]: Operation {req.operation_id} already consumed in Epoch {req.epoch}")
                self._respond(400, {"status": DENY_REPLAYED_OPERATION})
                return

            # 6. Signature Verification
            if not verify_signature(req.signing_key_public, req.signature, req.canonical_bytes()):
                print(f"[!] GATE DENIAL [DENY_BAD_SIGNATURE]")
                self._respond(400, {"status": DENY_BAD_SIGNATURE})
                return

            # ALLOW! Consume Operation ID and Issue Signed ConsequencePermit
            CONSUMED_OPERATIONS.add(op_key)

            permit = ConsequencePermit(
                execution_id=req.execution_id,
                epoch=req.epoch,
                holder_id=req.holder_id,
                operation_id=req.operation_id,
                state_root=req.state_root,
                evidence_head=req.evidence_head
            )
            permit.authority_signature = sign_bytes(AUTH_SIGNING_KEY, permit.canonical_bytes())

            print(f"[+] GATE ALLOWED: [{req.holder_id} Epoch {req.epoch} Op {req.operation_id}] -> Permit Issued")
            self._respond(200, {
                "status": ALLOW,
                "permit": permit.to_dict(),
                "authority_service_key": AUTH_PUB_HEX
            })

        elif action == "revoke_node":
            node_id = data.get("node_id")
            if node_id:
                REVOKED_NODES.add(node_id)
                print(f"[!] REVOCATION COMMITTED: Node '{node_id}' added to REVOKED_NODES set.")
                self._respond(200, {"status": "SUCCESS", "revoked_node": node_id})
            else:
                self._respond(400, {"status": "MISSING_NODE_ID"})

        elif action == "update_node_ceiling":
            node_id = data.get("node_id")
            ceiling = data.get("ceiling")
            if node_id and ceiling is not None:
                NODE_CEILINGS[node_id] = set(ceiling)
                print(f"[!] LIVE ANCESTOR CEILING MUTATED: Node '{node_id}' ceiling updated to {ceiling}")
                self._respond(200, {"status": "SUCCESS", "node_id": node_id, "current_ceiling": list(NODE_CEILINGS[node_id])})
            else:
                self._respond(400, {"status": "MISSING_NODE_ID_OR_CEILING"})

        elif action == "validate_recursive_consequence":
            req = RecursiveConsequenceRequest.from_dict(data["request"])
            current_rec = AUTHORITY_STORE.get(req.execution_id)
            if not current_rec:
                self._respond(400, {"status": "DENY_EXECUTION_NOT_FOUND"})
                return

            # 1. Epoch Fencing
            if req.epoch != current_rec.current_epoch:
                print(f"[!] GATE DENIAL [DENY_STALE_EPOCH]: Request Epoch {req.epoch} != Authority Epoch {current_rec.current_epoch}")
                self._respond(400, {"status": DENY_STALE_EPOCH, "current_epoch": current_rec.current_epoch})
                return

            # 2. Replay Fencing
            op_key = (req.execution_id, req.epoch, req.operation_id)
            if op_key in CONSUMED_OPERATIONS:
                print(f"[!] GATE DENIAL [DENY_REPLAYED_OPERATION]: Operation {req.operation_id} already consumed in Epoch {req.epoch}")
                self._respond(400, {"status": DENY_REPLAYED_OPERATION})
                return

            # 3. Recursive Lineage, Revocation, Static & Live Ancestor Ceiling Validation
            for cert_dict in req.delegation_chain:
                cert = DelegationCertificate.from_dict(cert_dict)
                # Check Revocation
                if cert.parent_id in REVOKED_NODES or cert.child_id in REVOKED_NODES:
                    print(f"[!] GATE DENIAL [DENY_REVOKED_LINEAGE]: Node lineage contains revoked node (parent: {cert.parent_id}, child: {cert.child_id})")
                    self._respond(400, {"status": "DENY_REVOKED_LINEAGE"})
                    return
                # Check Parent Signature
                if not verify_signature(cert.parent_public_key, cert.parent_signature, cert.canonical_bytes()):
                    print(f"[!] GATE DENIAL [DENY_BAD_SIGNATURE]: Bad signature in delegation cert for child {cert.child_id}")
                    self._respond(400, {"status": DENY_BAD_SIGNATURE})
                    return
                # Check Static Credential Ceiling Limit
                if req.target_resource not in cert.ceiling:
                    print(f"[!] GATE DENIAL [DENY_CEILING_EXCEEDED]: Target resource '{req.target_resource}' not in static delegation ceiling {cert.ceiling}")
                    self._respond(400, {"status": "DENY_CEILING_EXCEEDED"})
                    return
                # Check LIVE CURRENT ANCESTOR CEILING (H3 Invariant)
                if cert.parent_id in NODE_CEILINGS and req.target_resource not in NODE_CEILINGS[cert.parent_id]:
                    print(f"[!] GATE DENIAL [DENY_ANCESTOR_CEILING]: Target resource '{req.target_resource}' excluded by current live ceiling of parent ancestor '{cert.parent_id}'")
                    self._respond(400, {"status": "DENY_ANCESTOR_CEILING"})
                    return
                if cert.child_id in NODE_CEILINGS and req.target_resource not in NODE_CEILINGS[cert.child_id]:
                    print(f"[!] GATE DENIAL [DENY_ANCESTOR_CEILING]: Target resource '{req.target_resource}' excluded by current live ceiling of ancestor '{cert.child_id}'")
                    self._respond(400, {"status": "DENY_ANCESTOR_CEILING"})
                    return

            # 4. Holder Signature Verification
            if not verify_signature(req.signing_key_public, req.signature, req.canonical_bytes()):
                print(f"[!] GATE DENIAL [DENY_BAD_SIGNATURE]: Bad signature on RecursiveConsequenceRequest")
                self._respond(400, {"status": DENY_BAD_SIGNATURE})
                return

            # ALLOW! Consume Operation ID and Issue Signed ConsequencePermit
            CONSUMED_OPERATIONS.add(op_key)

            permit = ConsequencePermit(
                execution_id=req.execution_id,
                epoch=req.epoch,
                holder_id=req.holder_id,
                operation_id=req.operation_id,
                state_root=req.state_root,
                evidence_head=req.evidence_head
            )
            permit.authority_signature = sign_bytes(AUTH_SIGNING_KEY, permit.canonical_bytes())

            print(f"[+] RECURSIVE GATE ALLOWED: [{req.holder_id} Epoch {req.epoch} Op {req.operation_id} Res {req.target_resource}] -> Permit Issued")
            self._respond(200, {
                "status": ALLOW,
                "permit": permit.to_dict(),
                "authority_service_key": AUTH_PUB_HEX
            })

        else:
            self._respond(400, {"status": "INVALID_ACTION"})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

def run_server(port=8020):
    server = ThreadingHTTPServer(("0.0.0.0", port), DecoupledAuthorityHandler)
    print(f"==========================================================")
    print(f" V-CHIP DECOUPLED AUTHORITY TRUTH SINK ONLINE (Port {port})")
    print(f" Authority Service Public Key: {AUTH_PUB_HEX[:16]}...")
    print(f" Mandatory Consequence Gate & Fencing Online")
    print(f"==========================================================")
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8020
    run_server(port)
