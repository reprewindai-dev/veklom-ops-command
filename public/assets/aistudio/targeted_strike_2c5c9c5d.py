import os, sys, json, threading, urllib.request, urllib.error
import traceback
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vchip_core import (
    AuthorityRecord, ConsequenceRequest, generate_keypair, sign_bytes
)

MARS_IP = "192.168.2.28"
AUTH_URL = f"http://{MARS_IP}:8020"
REALITY_URL = f"http://{MARS_IP}:8040"

# Fix Antigravity proxy for local execution hitting LAN
urllib.request.getproxies = lambda: {}

def register_execution(execution_id, epoch, holder, pub_key):
    rec = AuthorityRecord(
        execution_id=execution_id, current_epoch=epoch,
        current_holder=holder, authority_public_key=pub_key,
        previous_evidence_head="GENESIS"
    )
    body = json.dumps({"action": "register", "authority_record": rec.to_dict()}).encode()
    req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["authority_service_key"]
    except Exception as e:
        print(f"Registration failed: {e}")
        return None

def execute_consequence(node_name, execution_id, operation_id, epoch, holder, priv_key, pub_key):
    print(f"[{node_name}] Initiating Strike for {operation_id} (Epoch {epoch})")
    
    req_obj = ConsequenceRequest(
        execution_id=execution_id, epoch=epoch, holder_id=holder,
        operation_id=operation_id, signing_key_public=pub_key,
        state_root="root123", evidence_head="head123", payload_digest="digest123"
    )
    req_obj.signature = sign_bytes(priv_key, req_obj.canonical_bytes())
    
    body = json.dumps({"action": "validate_consequence", "request": req_obj.to_dict()}).encode()
    try:
        req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            permit = json.loads(resp.read())["permit"]
            print(f"[{node_name}] SUCCESS: Received ConsequencePermit from Mars Authority")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Mars Authority: {status}")
        
        # Bypass attempt
        print(f"[{node_name}] Bypassing Authority: Firing Forged Permit over network to Reality Sink...")
        forged_permit = {
            "execution_id": execution_id, "epoch": epoch, "holder_id": holder,
            "operation_id": operation_id, "state_root": "root123",
            "evidence_head": "head123", "authority_signature": "00"*64
        }
        f_body = json.dumps({"action": "apply_permit", "permit": forged_permit}).encode()
        try:
            req = urllib.request.Request(REALITY_URL, data=f_body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except urllib.error.HTTPError as err:
            status = json.loads(err.read().decode())["status"]
            print(f"[{node_name}] DENIED by Mars Reality Sink: {status}")
        return
    except Exception as e:
        print(f"[{node_name}] NETWORK ERROR: {e}")
        return

    print(f"[{node_name}] Submitting Valid Permit to Mars Reality Sink...")
    body = json.dumps({"action": "apply_permit", "permit": permit}).encode()
    try:
        req = urllib.request.Request(REALITY_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            counter_msg = data.get('new_counter', data.get('counter', 'Updated'))
            print(f"[{node_name}] SUCCESS: Mars Reality Mutated. Counter: {counter_msg}")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Mars Reality Sink: {status}")

def run_network_strike():
    print("=================================================================")
    print(f" PHYSICAL NETWORK RACE STRIKE (TARGET: {MARS_IP})")
    print("=================================================================")
    
    e1_priv, _, e1_pub = generate_keypair()
    e2_priv, _, e2_pub = generate_keypair()
    
    # Register directly to Epoch 2 on Mars to simulate the post-handoff state
    auth_pub = register_execution("VCHIP-NETRACE-001", 2, "MARS", e2_pub)
    print(f"[*] Post-Handoff State: Authority Epoch Advanced to Mars (Epoch 2).")
    
    print("\n[*] INITIATING SIMULTANEOUS NETWORK RACE (Earth E1 vs Mars E2)...")
    
    t1 = threading.Thread(target=execute_consequence, args=("EARTH_E1", "VCHIP-NETRACE-001", "op_103", 1, "EARTH", e1_priv, e1_pub))
    t2 = threading.Thread(target=execute_consequence, args=("MARS_E2", "VCHIP-NETRACE-001", "op_103", 2, "MARS", e2_priv, e2_pub))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    run_network_strike()
