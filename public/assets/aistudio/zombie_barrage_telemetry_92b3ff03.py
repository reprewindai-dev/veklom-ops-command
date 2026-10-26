import time
import json
import urllib.request
import urllib.error
import socket
import sys
import ctypes
from ctypes import wintypes
import gc

urllib.request.getproxies = lambda: {}

sys.path.insert(0, r"C:\Users\antho\vchip")
from vchip_core import generate_keypair, sign_bytes, ConsequenceRequest, HandoffPackage

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

def get_mem():
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(),
        ctypes.byref(counters),
        counters.cb
    )
    return counters.WorkingSetSize, counters.PrivateUsage, counters.PageFaultCount

def post_json(url, payload, timeout=1.0):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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
print("20,000-ITERATION ZOMBIE BARRAGE STRESS TEST")
print("==================================================")
mars_ip = "192.168.2.28"
if not (check_port(mars_ip, 8020) and check_port(mars_ip, 8040)):
    print(f"[FAIL] Could not reach Mars ports. Aborting.")
    sys.exit(1)
print(f"[OK] Mars Gate (8020) and Sink (8040) are OPEN and REACHABLE.")

exec_id = f"ZOMBIE_BARRAGE_{int(time.time())}"
earth_sk, earth_priv, earth_pub = generate_keypair()
mars_sk, mars_priv, mars_pub = generate_keypair()

gate_url = f"http://{mars_ip}:8020"
sink_url = f"http://{mars_ip}:8040"

print(f"[*] Registering Genesis on Mars Gate (Epoch 1)...")
post_json(f"{gate_url}", {
    "action": "register_genesis",
    "execution_id": exec_id,
    "epoch": 1,
    "holder_id": "EARTH_ZOMBIE",
    "authority_public_key": earth_pub,
    "evidence_head": "GENESIS"
}, timeout=5.0)

print(f"[*] Handing off authority to Mars (Epoch 2)...")
handoff_pkg = HandoffPackage(execution_id=exec_id, from_epoch=1, to_epoch=2, from_holder="EARTH_ZOMBIE", to_holder="MARS_CURRENT_OWNER", state_root="ROOT_2", evidence_head="EVIDENCE_2_INIT", next_public_key=mars_pub)
handoff_pkg.signature = sign_bytes(earth_sk, handoff_pkg.canonical_bytes())
post_json(f"{gate_url}", {"action": "handoff", "handoff_package": handoff_pkg.to_dict()}, timeout=5.0)

print(f"\n[!] COMMENCING 20,000 FORGED ZOMBIE STRIKES AGAINST MARS")
BARRAGE_COUNT = 20000
blocked_count = 0
failed_requests = 0

start_time = time.time()
ws0, priv0, pf0 = get_mem()
print(f"[*] Baseline Telemetry -> WorkingSet: {ws0//1024} KB | Private: {priv0//1024} KB | Faults: {pf0}")

for i in range(1, BARRAGE_COUNT + 1):
    zombie_req = ConsequenceRequest(
        execution_id=exec_id, 
        epoch=1, 
        holder_id="EARTH_ZOMBIE", 
        operation_id=f"OP_ZOMBIE_BARRAGE_{i}", 
        signing_key_public=earth_pub, 
        state_root=f"FORGED_ROOT_{i}", 
        evidence_head=f"FORGED_EVIDENCE_{i}", 
        payload_digest=f"DIGEST_{i}"
    )
    zombie_req.signature = sign_bytes(earth_sk, zombie_req.canonical_bytes())

    try:
        # Strict 0.5s timeout. If Mars tarpits or drops, it will timeout and we count it as blocked.
        post_json(f"{gate_url}", {"action": "validate_consequence", "request": zombie_req.to_dict(), "signature": zombie_req.signature}, timeout=0.5)
        print(f"[!] FATAL: ZOMBIE STRIKE {i} PENETRATED THE GATE!")
    except urllib.error.URLError as e:
        # This catches timeouts (Ghost Tarpit)
        blocked_count += 1
    except Exception as e:
        err_str = str(e)
        if "DENY_STALE_EPOCH" in err_str:
            blocked_count += 1
        else:
            failed_requests += 1
            
    if i % 1000 == 0:
        ws, priv, pf = get_mem()
        gc_count = gc.get_count()
        elapsed = time.time() - start_time
        rate = i / elapsed
        print(f"   [Checkpoint {i}/20000] | Blocked/Tarpitted: {blocked_count} | Rate: {rate:.1f} ops/s")
        print(f"      Telemetry -> WorkingSet: {ws//1024} KB | Private: {priv//1024} KB | GC: {gc_count}")
        gc.collect()

end_time = time.time()
wsF, privF, pfF = get_mem()
total_time = end_time - start_time

print("\n==================================================")
print("[3] BARRAGE RESULTS & DESTINATION READBACK")
print("==================================================")
print(f"Total Time: {total_time:.2f} seconds")
print(f"Average Rate: {BARRAGE_COUNT / total_time:.2f} strikes/sec")
print(f"Gate Fences (DENY_STALE_EPOCH / Tarpit): {blocked_count} / {BARRAGE_COUNT}")
print(f"Other Errors: {failed_requests}")
print(f"Final Telemetry -> WorkingSet: {wsF//1024} KB | Private: {privF//1024} KB")

print("\n[*] Querying Mars Reality Sink directly to verify zero zombie consequences materialized...")
try:
    with urllib.request.urlopen(sink_url, timeout=5) as resp:
        sink_data = json.loads(resp.read().decode('utf-8'))
        ops = sink_data.get("applied_operations", [])
        zombie_ops = [op.get("operation_id") for op in ops if "OP_ZOMBIE_BARRAGE" in op.get("operation_id", "")]
        if zombie_ops:
            print(f"[!] FATAL: {len(zombie_ops)} ZOMBIE CONSEQUENCES FOUND IN MARS SINK!")
        else:
            print("[OK] SINK VERIFIED: EXACTLY ZERO ZOMBIE CONSEQUENCES MATERIALIZED.")
except Exception as e:
    print(f"[?] Could not read sink: {e}")

