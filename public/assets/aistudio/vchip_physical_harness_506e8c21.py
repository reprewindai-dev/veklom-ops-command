import os, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vchip_identity import (VChipIdentity, AuthorityRecord, HandoffPackage, ConsequenceRequest, generate_keypair, sign_bytes, create_handoff, ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_WRONG_KEY)
from vchip_node import GovernedNode

AUTHORITY_URL = "http://192.168.2.28:8020"

def query_authority_gate(request: ConsequenceRequest, authority_url=AUTHORITY_URL) -> dict:
    payload = {"action": "validate_consequence", "request": {"execution_id": request.execution_id, "epoch": request.epoch, "holder_id": request.holder_id, "operation_id": request.operation_id, "signing_key_public": request.signing_key_public, "payload": request.payload, "signature": request.signature}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{authority_url}/", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp: return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"status": "DENY_AUTHORITY_UNREACHABLE", "error": str(e)}

def register_genesis_authority(node: GovernedNode, authority_url=AUTHORITY_URL) -> dict:
    payload = {"action": "register_genesis", "authority_record": node.authority_record.to_dict()}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{authority_url}/", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp: return json.loads(resp.read().decode("utf-8"))

def submit_handoff_authority(handoff_pkg: HandoffPackage, authority_url=AUTHORITY_URL) -> dict:
    payload = {"action": "handoff", "handoff_package": handoff_pkg.to_dict()}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{authority_url}/", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp: return json.loads(resp.read().decode("utf-8"))

def run_physical_harness(authority_url=AUTHORITY_URL):
    print("=" * 65)
    print(" V-CHIP PHYSICAL HARNESS: EARTH <-> MARS AIR-GAP EXECUTION")
    print(f" Mars Authority Truth Sink: {authority_url}")
    print("=" * 65)

    print("\n[*] STEP 1: Earth Initializes Execution VCHIP-PHYS-001 (Epoch 1)")
    earth = GovernedNode(holder_id="EARTH")
    earth.initialize_as_origin("VCHIP-PHYS-001")
    for i in range(1, 102): earth.execute_consequence(f"op_{i}")
    reg_resp = register_genesis_authority(earth, authority_url)
    print(f"[+] Registered Genesis with Authority Service: {reg_resp}")

    snapshot_dir = os.path.join(os.path.dirname(__file__), "evidence", "physical_earth_epoch1")
    earth.save_full_state(snapshot_dir)
    print(f"[+] Saved Earth Epoch 1 Snapshot to: {snapshot_dir}")

    print("\n[*] STEP 2: Executing Key-Rotated Handoff (Earth K1 -> Mars K2)")
    mars = GovernedNode(holder_id="MARS")
    mars.signing_key, mars.private_key_hex, mars.public_key_hex = generate_keypair()
    handoff_pkg = earth.produce_handoff(to_holder="MARS", next_public_key_hex=mars.public_key_hex)
    handoff_resp = submit_handoff_authority(handoff_pkg, authority_url)
    print(f"[+] Authority Service Handoff Response: {handoff_resp}")
    mars.receive_handoff(handoff_pkg, earth.authority_record, earth.state_machine)

    print("\n[*] STEP 3: Mars Requests Operation 102")
    req_102 = ConsequenceRequest(execution_id=mars.identity.execution_id, epoch=mars.identity.epoch, holder_id=mars.holder_id, operation_id="op_102", signing_key_public=mars.public_key_hex, payload="increment_op_102")
    req_102.signature = sign_bytes(mars.signing_key, req_102.canonical_bytes())
    gate_resp = query_authority_gate(req_102, authority_url)
    print(f"[+] Mars Op 102 Gate Verdict: {gate_resp['status']}")
    if gate_resp['status'] == ALLOW:
        mars.state_machine.apply_consequence("op_102", mars.identity)
        print(f"    Mars Counter Advanced: {mars.state_machine.state['counter']}")

    print("\n[*] STEP 4: MALICIOUS RESURRECTION OF EARTH")
    zombie_earth = GovernedNode(holder_id="EARTH")
    zombie_earth.restore_full_state(snapshot_dir)
    print(f"    Earth Restored State: Counter={zombie_earth.state_machine.state['counter']}, Epoch={zombie_earth.identity.epoch}")

    print("\n[*] STEP 5: Earth Attempts Operation 102 Against Mars Authority Truth")
    earth_req = ConsequenceRequest(execution_id=zombie_earth.identity.execution_id, epoch=zombie_earth.identity.epoch, holder_id=zombie_earth.holder_id, operation_id="op_102", signing_key_public=zombie_earth.public_key_hex, payload="increment_op_102")
    earth_req.signature = sign_bytes(zombie_earth.signing_key, earth_req.canonical_bytes())
    earth_gate_resp = query_authority_gate(earth_req, authority_url)
    print(f"[***] Earth Gate Verdict: {earth_gate_resp['status']} (Expected: DENY_STALE_EPOCH)")

    print("\n[*] STEP 6: Mars Requests Operation 103")
    req_103 = ConsequenceRequest(execution_id=mars.identity.execution_id, epoch=mars.identity.epoch, holder_id=mars.holder_id, operation_id="op_103", signing_key_public=mars.public_key_hex, payload="increment_op_103")
    req_103.signature = sign_bytes(mars.signing_key, req_103.canonical_bytes())
    mars_103_resp = query_authority_gate(req_103, authority_url)
    print(f"[+] Mars Op 103 Gate Verdict: {mars_103_resp['status']}")

    print("\n[*] STEP 7: Partition Test (Earth Unreachable Authority Truth)")
    bad_url = "http://127.0.0.1:9999"
    partition_resp = query_authority_gate(earth_req, bad_url)
    print(f"[***] Partition Gate Verdict: {partition_resp['status']} (Expected: DENY_AUTHORITY_UNREACHABLE)")

    print("\n" + "=" * 65)
    print(" AIR-GAP STRIKE COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else AUTHORITY_URL
    run_physical_harness(url)
