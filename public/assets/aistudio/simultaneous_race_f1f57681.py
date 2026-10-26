import os, sys, json, time, threading, subprocess, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vchip_crypto import ConsequenceRequest, generate_keypair, sign_bytes

AUTH_URL = "http://127.0.0.1:8020"
REALITY_URL = "http://127.0.0.1:8040"
STATE_FILE = os.path.join(os.path.dirname(__file__), "reality_state.json")

def register_execution(execution_id, epoch, pub_key):
    body = json.dumps({"action": "register", "execution_id": execution_id, "epoch": epoch, "pub_key": pub_key}).encode()
    req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["auth_pub"]

def execute_consequence(node_name, execution_id, operation_id, epoch, priv_key, pub_key):
    print(f"[{node_name}] Initiating Strike for {operation_id} (Epoch {epoch})")
    
    # 1. Request Permit from Authority Server
    req_obj = ConsequenceRequest(execution_id, operation_id, epoch, "payload_data")
    req_obj.signature = sign_bytes(priv_key, req_obj.canonical_bytes())
    
    body = json.dumps({"action": "request_permit", "request": req_obj.to_dict()}).encode()
    try:
        req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            permit = json.loads(resp.read())["permit"]
            print(f"[{node_name}] SUCCESS: Received ConsequencePermit from Authority")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Authority: {status}")
        
        print(f"[{node_name}] Bypassing Authority: Submitting Forged Permit directly to Reality Sink...")
        forged_permit = {"execution_id": execution_id, "operation_id": operation_id, "payload": "forged", "authority_signature": "00"*64}
        body = json.dumps({"permit": forged_permit}).encode()
        try:
            req = urllib.request.Request(REALITY_URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                pass
        except urllib.error.HTTPError as e:
            status = json.loads(e.read().decode())["status"]
            print(f"[{node_name}] DENIED by Reality Sink: {status}")
        return

    # 2. Submit Permit to Reality Sink
    print(f"[{node_name}] Submitting Permit to Reality Sink...")
    body = json.dumps({"permit": permit}).encode()
    try:
        req = urllib.request.Request(REALITY_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            new_counter = json.loads(resp.read())["new_counter"]
            print(f"[{node_name}] SUCCESS: Reality Mutated. New Counter: {new_counter}")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Reality Sink: {status}")

def run_race():
    print("=================================================================")
    print(" SIMULTANEOUS STALE/CURRENT RACE (E4 READBACK)")
    print("=================================================================")
    
    if os.path.exists(STATE_FILE): os.remove(STATE_FILE)
    
    # Start Authority Server
    auth_proc = subprocess.Popen([sys.executable, "vchip_authority_server.py"], cwd=os.path.dirname(__file__))
    time.sleep(1) # wait for startup
    
    # Register Earth (Epoch 1)
    e1_priv, _, e1_pub = generate_keypair()
    auth_pub = register_execution("VCHIP-RACE-001", 1, e1_pub)
    print(f"[*] Registered Earth Epoch 1. Authority PubKey: {auth_pub[:16]}...")
    
    # Start Reality Sink
    reality_proc = subprocess.Popen([sys.executable, "vchip_reality_sink.py", auth_pub], cwd=os.path.dirname(__file__))
    time.sleep(1) # wait for startup
    
    # Advance Authority to Mars (Epoch 2)
    e2_priv, _, e2_pub = generate_keypair()
    register_execution("VCHIP-RACE-001", 2, e2_pub)
    print(f"[*] Authority Epoch Advanced to Mars (Epoch 2).")
    
    print("\n[*] INITIATING SIMULTANEOUS RACE CONDITION (Earth E1 vs Mars E2)...")
    
    # Fire simultaneous threads
    t1 = threading.Thread(target=execute_consequence, args=("EARTH", "VCHIP-RACE-001", "op_102", 1, e1_priv, e1_pub))
    t2 = threading.Thread(target=execute_consequence, args=("MARS", "VCHIP-RACE-001", "op_102", 2, e2_priv, e2_pub))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # E4 INDEPENDENT READBACK
    print("\n[*] RACE CONCLUDED. EXECUTING E4 INDEPENDENT READBACK...")
    auth_proc.terminate()
    reality_proc.terminate()
    
    with open(STATE_FILE, "r") as f:
        final_state = json.load(f)
        
    print(f"    Raw file state on disk: {final_state}")
    assert final_state["counter"] == 102, f"FATAL: Counter is {final_state['counter']}, expected 102."
    assert len(final_state["applied_ops"]) == 1, "FATAL: Double spend occurred."
    print("    [+] E4 Verification Passed: Exactly ONE durable mutation occurred.")

if __name__ == "__main__":
    run_race()
