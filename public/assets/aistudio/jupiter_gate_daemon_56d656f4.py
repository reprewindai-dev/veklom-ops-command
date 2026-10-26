import os
import sys
import json
import struct
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

for p in [r"C:\Users\antho\scratch\pylibs", r"C:\Users\antho\vchip", os.path.dirname(os.path.abspath(__file__))]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from vchip_core import (
    AuthorityRecord, ConsequenceRequest, ConsequencePermit,
    generate_keypair, sign_bytes, verify_signature,
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_WRONG_KEY,
    DENY_BAD_SIGNATURE, DENY_WRONG_EXECUTION, DENY_REPLAYED_OPERATION
)

AUTHORITY_STORE = {}
CONSUMED_OPERATIONS = set()
AUTH_SIGNING_KEY, AUTH_PRIV_HEX, AUTH_PUB_HEX = generate_keypair()
SINK_PORT = 8040

class VoidAuthorityGateHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        exec_id = self.path.strip("/")
        if exec_id in AUTHORITY_STORE:
            self._respond_json(200, AUTHORITY_STORE[exec_id].to_dict())
        else:
            self._respond_json(404, {"error": "EXECUTION_NOT_FOUND"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._respond_text(400, "ERROR: empty_payload")
            return

        raw_body = self.rfile.read(content_length)

        # Detect 0x51 Binary Envelope
        if len(raw_body) >= 5 and raw_body[0] == 0x51:
            try:
                magic, packet_len = struct.unpack("!BI", raw_body[:5])
                if magic != 0x51:
                    self._respond_text(422, "ERROR: invalid_inner_geometry")
                    return
                json_bytes = raw_body[5:5 + packet_len]
                data = json.loads(json_bytes.decode("utf-8"))
                self._handle_unwrapped_payload(data)
            except json.decoder.JSONDecodeError:
                self._respond_text(500, "ERROR: structural_parse_failure")
            except Exception as e:
                self._respond_text(500, f"ERROR: internal_failure: {e}")
            return

        # Fallback to standard JSON POST
        try:
            data = json.loads(raw_body.decode("utf-8"))
            self._handle_standard_json(data)
        except Exception as e:
            self._respond_json(400, {"status": "INVALID_JSON_OR_BODY", "error": str(e)})

    def _handle_unwrapped_payload(self, data):
        # Extract request components whether nested or flat
        req_dict = data.get("consequence_request") or data.get("request") or data
        exec_id = req_dict.get("execution_id", "DEFAULT")
        epoch = req_dict.get("epoch", 5)
        holder = req_dict.get("holder_id") or req_dict.get("holder", "VOID_WORKER")
        op_id = req_dict.get("operation_id", "")
        pub_key = req_dict.get("signing_key_public") or req_dict.get("pub_key", "")
        state_root = req_dict.get("state_root", "R1")
        evidence_head = req_dict.get("evidence_head", "E2")
        payload_digest = req_dict.get("payload_digest", "P3")
        sig = req_dict.get("signature") or req_dict.get("signature_hex", "")

        # If execution not registered yet, auto-register for naive host resurrection
        if exec_id not in AUTHORITY_STORE:
            rec = AuthorityRecord(
                execution_id=exec_id,
                current_epoch=epoch,
                current_holder=holder,
                authority_public_key=pub_key,
                previous_evidence_head=evidence_head
            )
            AUTHORITY_STORE[exec_id] = rec
            print(f"[*] Gate Auto-Registered Genesis for {exec_id} at Epoch {epoch}", flush=True)

        current_rec = AUTHORITY_STORE[exec_id]

        # 1. Epoch Fencing
        if epoch != current_rec.current_epoch:
            print(f"[!] Gate DENY_STALE_EPOCH: {epoch} != {current_rec.current_epoch}", flush=True)
            self._respond_json(400, {"status": DENY_STALE_EPOCH, "current_epoch": current_rec.current_epoch})
            return

        # 2. Holder Fencing
        if holder != current_rec.current_holder:
            print(f"[!] Gate DENY_WRONG_HOLDER: {holder} != {current_rec.current_holder}", flush=True)
            self._respond_json(400, {"status": DENY_WRONG_HOLDER})
            return

        # 3. Key Fencing
        if pub_key != current_rec.authority_public_key:
            print(f"[!] Gate DENY_WRONG_KEY", flush=True)
            self._respond_json(400, {"status": DENY_WRONG_KEY})
            return

        # 4. Replay Fencing
        op_key = (exec_id, epoch, op_id)
        if op_key in CONSUMED_OPERATIONS:
            print(f"[!] Gate DENY_REPLAYED_OPERATION: {op_id}", flush=True)
            self._respond_json(400, {"status": DENY_REPLAYED_OPERATION})
            return

        # 5. Ed25519 Detached Signature Verification
        canonical_d = {
            "execution_id": exec_id,
            "epoch": epoch,
            "holder_id": holder,
            "operation_id": op_id,
            "signing_key_public": pub_key,
            "state_root": state_root,
            "evidence_head": evidence_head,
            "payload_digest": payload_digest,
        }
        canonical_raw1 = json.dumps(canonical_d, sort_keys=True).encode("utf-8")
        canonical_raw2 = json.dumps(canonical_d, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if not (verify_signature(pub_key, sig, canonical_raw1) or verify_signature(pub_key, sig, canonical_raw2)):
            print(f"[!] Gate DENY_BAD_SIGNATURE", flush=True)
            self._respond_json(400, {"status": DENY_BAD_SIGNATURE})
            return

        # Commit Operation & Issue Consequence Permit
        CONSUMED_OPERATIONS.add(op_key)
        permit = ConsequencePermit(
            execution_id=exec_id,
            epoch=epoch,
            holder_id=holder,
            operation_id=op_id,
            state_root=state_root,
            evidence_head=evidence_head
        )
        permit.authority_signature = sign_bytes(AUTH_SIGNING_KEY, permit.canonical_bytes())
        print(f"[+] Gate ALLOWED: [{holder} Epoch {epoch} Op {op_id}] -> Permit Issued", flush=True)

        # Forward consequence collapse directly to local Reality Sink
        self._forward_to_local_sink(permit)

        # Return ALLOW and SUCCESS_COLLAPSE_LOGGED confirmation
        self._respond_json(200, {
            "status": ALLOW,
            "permit": permit.to_dict(),
            "message": "SUCCESS_COLLAPSE_LOGGED",
            "authority_service_key": AUTH_PUB_HEX
        })

    def _forward_to_local_sink(self, permit):
        try:
            sink_url = f"http://127.0.0.1:{SINK_PORT}/"
            sink_payload = json.dumps({"action": "apply_permit", "permit": permit.to_dict()}).encode("utf-8")
            req = urllib.request.Request(sink_url, data=sink_payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                print(f"[+] Gate auto-forwarded permit to local Sink: HTTP {resp.status}", flush=True)
        except Exception as e:
            print(f"[*] Local sink forwarding note: {e} (Transmitter will handle permit application directly if needed)", flush=True)

    def _handle_standard_json(self, data):
        action = data.get("action")
        if action in ("register_genesis", "register"):
            exec_id = data.get("execution_id", "DEFAULT")
            epoch = data.get("epoch", 1)
            holder = data.get("holder") or data.get("holder_id") or "VOID_WORKER"
            pub_key = data.get("pub_key") or data.get("authority_public_key", "")
            rec = AuthorityRecord(
                execution_id=exec_id,
                current_epoch=epoch,
                current_holder=holder,
                authority_public_key=pub_key,
                previous_evidence_head="GENESIS"
            )
            AUTHORITY_STORE[exec_id] = rec
            print(f"[*] Registered Genesis: {exec_id} | Epoch {epoch} | Key: {pub_key[:16]}...", flush=True)
            self._respond_json(200, {"status": "SUCCESS", "epoch": epoch, "authority_service_key": AUTH_PUB_HEX})
        elif action == "validate_consequence":
            req_dict = data.get("consequence_request") or data.get("request") or {}
            self._handle_unwrapped_payload(req_dict)
        else:
            self._respond_json(400, {"status": "INVALID_ACTION"})

    def _respond_json(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def _respond_text(self, code, text):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

def main():
    global SINK_PORT
    gate_port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8020
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        SINK_PORT = int(sys.argv[2])
    server = ThreadingHTTPServer(("0.0.0.0", gate_port), VoidAuthorityGateHandler)
    print(f"[*] Jupiter V-Chip Gate online at 0.0.0.0:{gate_port} (0x51 + JSON enabled)", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()
