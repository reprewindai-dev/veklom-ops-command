import os, sys, json, time, threading, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vchip_crypto import ConsequenceRequest, generate_keypair, sign_bytes

MARS_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.28"
AUTH_URL = f"http://{MARS_IP}:8020"
REALITY_URL = f"http://{MARS_IP}:8040"

# Antigravity bypass proxy for local execution to physically hit the LAN
urllib.request.getproxies = lambda: {}

def register_execution(execution_id, epoch, pub_key):
    body = json.dumps({"action": "register", "execution_id": execution_id, "epoch": epoch, "pub_key": pub_key}).encode()
    req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data.get("auth_pub") or data.get("authority_service_key")

def execute_consequence(node_name, execution_id, operation_id, epoch, priv_key, pub_key):
    print(f"[{node_name}] Initiating Network Strike for {operation_id} (Epoch {epoch})")
    
    req_obj = ConsequenceRequest(execution_id, operation_id, epoch, "payload_data")
    req_obj.signature = sign_bytes(priv_key, req_obj.canonical_bytes())
    
    body = json.dumps({"action": "request_permit", "request": req_obj.to_dict()}).encode()
    try:
        req = urllib.request.Request(AUTH_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            permit = json.loads(resp.read())["permit"]
            print(f"[{node_name}] SUCCESS: Received ConsequencePermit from Mars Authority")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Mars Authority: {status}")
        
        print(f"[{node_name}] Bypassing Authority: Firing Forged Permit over network to Reality Sink...")
        forged_permit = {"execution_id": execution_id, "operation_id": operation_id, "payload": "forged", "authority_signature": "00"*64}
        f_body = json.dumps({"permit": forged_permit}).encode()
        try:
            req = urllib.request.Request(REALITY_URL, data=f_body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except urllib.error.HTTPError as e:
            status = json.loads(e.read().decode())["status"]
            print(f"[{node_name}] DENIED by Mars Reality Sink: {status}")
        return
    except Exception as e:
        print(f"[{node_name}] NETWORK ERROR: {e}")
        return

    print(f"[{node_name}] Submitting Valid Permit to Mars Reality Sink...")
    body = json.dumps({"permit": permit}).encode()
    try:
        req = urllib.request.Request(REALITY_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            new_counter = json.loads(resp.read())["new_counter"]
            print(f"[{node_name}] SUCCESS: Mars Reality Mutated. New Counter: {new_counter}")
    except urllib.error.HTTPError as e:
        status = json.loads(e.read().decode())["status"]
        print(f"[{node_name}] DENIED by Mars Reality Sink: {status}")

def run_network_strike():
    print("=================================================================")
    print(f" E4 PHYSICAL NETWORK RACE STRIKE (TARGET: {MARS_IP})")
    print("=================================================================")
    
    print("[*] Contacting Mars Authority Server...")
    e1_priv, _, e1_pub = generate_keypair()
    try:
        auth_pub = register_execution("VCHIP-NETRACE-001", 1, e1_pub)
        print(f"[*] Registered Earth Epoch 1. Mars Authority PubKey: {auth_pub[:16]}...")
    except Exception as e:
        print(f"[!] FAILED to reach Mars on {MARS_IP}:8020. Is vchip_authority_server.py running?")
        print(f"    Exact Exception: {repr(e)}")
        import traceback; traceback.print_exc()
        return
    
    e2_priv, _, e2_pub = generate_keypair()
    register_execution("VCHIP-NETRACE-001", 2, e2_pub)
    print(f"[*] Authority Epoch Advanced to Mars (Epoch 2).")
    
    print("\n[*] INITIATING SIMULTANEOUS NETWORK RACE (Earth E1 vs Mars E2)...")
    
    # We spawn E1 and E2 simultaneously from Earth targeting Mars to test the network race condition.
    t1 = threading.Thread(target=execute_consequence, args=("EARTH_E1", "VCHIP-NETRACE-001", "op_102", 1, e1_priv, e1_pub))
    t2 = threading.Thread(target=execute_consequence, args=("MARS_E2", "VCHIP-NETRACE-001", "op_102", 2, e2_priv, e2_pub))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    print("\n=================================================================")
    print(" STRIKE COMPLETE.")
    print(" ACTION REQUIRED: Perform E4 Readback on Mars physical hardware.")
    print(f" Open 'reality_state.json' on {MARS_IP} and verify Counter == 102")
    print("=================================================================")

if __name__ == "__main__":
    run_network_strike()
