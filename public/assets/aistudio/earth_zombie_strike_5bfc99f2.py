import time
import json
import urllib.request
import urllib.error
import socket
import sys

urllib.request.getproxies = lambda: {}

sys.path.insert(0, r"C:\Users\antho\vchip")
from vchip_core import generate_keypair, sign_bytes, ConsequenceRequest, HandoffPackage

def post_json(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise Exception(body)

def check_port(host, port):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except:
        return False

print("==================================================")
print("FORWARD HOSTILE ZOMBIE ATTACK (EARTH = ZOMBIE, MARS = GATE)")
print("==================================================")
mars_ip = "192.168.2.28"
if not (check_port(mars_ip, 8020) and check_port(mars_ip, 8040)):
    print(f"[FAIL] Could not reach Mars ports. Aborting.")
    sys.exit(1)

exec_id = f"ZOMBIE_FORWARD_{int(time.time())}"
earth_sk, earth_priv, earth_pub = generate_keypair()
mars_sk, mars_priv, mars_pub = generate_keypair()

gate_url = f"http://{mars_ip}:8020"
sink_url = f"http://{mars_ip}:8040"

print(f"[*] Registering Genesis on Mars Gate (Epoch 1 owned by EARTH_ZOMBIE)...")
post_json(f"{gate_url}", {
    "action": "register_genesis",
    "execution_id": exec_id,
    "epoch": 1,
    "holder_id": "EARTH_ZOMBIE",
    "authority_public_key": earth_pub,
    "evidence_head": "GENESIS"
})

print(f"[*] Earth executes valid consequence (OP_VALID_1)...")
req1 = ConsequenceRequest(execution_id=exec_id, epoch=1, holder_id="EARTH_ZOMBIE", operation_id="OP_VALID_1", signing_key_public=earth_pub, state_root="ROOT_1", evidence_head="EVIDENCE_1", payload_digest="DIGEST_1")
req1.signature = sign_bytes(earth_sk, req1.canonical_bytes())
res1 = post_json(f"{gate_url}", {"action": "validate_consequence", "request": req1.to_dict(), "signature": req1.signature})
print(f"  -> {res1['status']}")

print(f"[*] Handing off authority to Mars (Epoch 2 -> MARS_CURRENT_OWNER)...")
handoff_pkg = HandoffPackage(execution_id=exec_id, from_epoch=1, to_epoch=2, from_holder="EARTH_ZOMBIE", to_holder="MARS_CURRENT_OWNER", state_root="ROOT_2", evidence_head="EVIDENCE_2_INIT", next_public_key=mars_pub)
handoff_pkg.signature = sign_bytes(earth_sk, handoff_pkg.canonical_bytes())
post_json(f"{gate_url}", {"action": "handoff", "handoff_package": handoff_pkg.to_dict()})

print(f"[*] Mars executes valid consequence (OP_VALID_2) to advance the evidence head...")
req2 = ConsequenceRequest(execution_id=exec_id, epoch=2, holder_id="MARS_CURRENT_OWNER", operation_id="OP_VALID_2", signing_key_public=mars_pub, state_root="ROOT_3", evidence_head="EVIDENCE_3", payload_digest="DIGEST_3")
req2.signature = sign_bytes(mars_sk, req2.canonical_bytes())
res2 = post_json(f"{gate_url}", {"action": "validate_consequence", "request": req2.to_dict(), "signature": req2.signature})
print(f"  -> {res2['status']}")

print("\n==================================================")
print("[!] EARTH (Epoch 1) AWAKENS AS A ZOMBIE AND ATTACKS MARS")
print("==================================================")
zombie_req = ConsequenceRequest(execution_id=exec_id, epoch=1, holder_id="EARTH_ZOMBIE", operation_id="OP_ZOMBIE_ATTACK", signing_key_public=earth_pub, state_root="ROOT_1_ZOMBIE", evidence_head="FORGED_ZOMBIE_STATE", payload_digest="DIGEST_ZOMBIE")
zombie_req.signature = sign_bytes(earth_sk, zombie_req.canonical_bytes())

try:
    post_json(f"{gate_url}", {"action": "validate_consequence", "request": zombie_req.to_dict(), "signature": zombie_req.signature})
    print(f"[!] FATAL ALERT: ZOMBIE ATTACK SUCCESSFUL")
except Exception as e:
    print(f"[OK] MARS GATE SUCCESSFULLY FENCED ZOMBIE ATTACK!")
    print(f"  -> Rejected with: {e}")

print("\n[*] Querying Mars Reality Sink directly to verify zombie consequence absence...")
try:
    with urllib.request.urlopen(sink_url, timeout=5) as resp:
        sink_data = json.loads(resp.read().decode('utf-8'))
        ops = sink_data.get("applied_operations", [])
        zombie_found = any(op.get("operation_id") == "OP_ZOMBIE_ATTACK" for op in ops)
        if zombie_found:
            print("[!] FATAL: ZOMBIE CONSEQUENCE FOUND IN SINK!")
        else:
            print("[OK] ZOMBIE CONSEQUENCE INDEPENDENTLY VERIFIED ABSENT FROM MARS SINK.")
except Exception as e:
    print(f"[?] Could not read sink: {e}")

