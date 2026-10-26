import sys, json, time, urllib.request, ctypes, gc, os
from ctypes import wintypes

urllib.request.getproxies = lambda: {}
sys.path.insert(0, 'C:\\Users\\antho\\vchip')

from vchip_core import generate_keypair, sign_bytes
from vfrac_recursive_core import RecursiveConsequenceRequest

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

def get_mem():
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    return counters.WorkingSetSize, counters.PrivateUsage, counters.PageFaultCount

def http_post(url, payload, timeout=60.0):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return 500, {"error": str(e)}

def fetch_mars_state(sink_url):
    try:
        with urllib.request.urlopen(urllib.request.Request(sink_url, method='GET'), timeout=10.0) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def execute_telemetry_strike(gate_url, sink_url, chunk_sizes=[2000, 4000, 10000], batch_size=100000):
    report = []
    
    for c_size in chunk_sizes:
        print(f"\n================================================================")
        print(f"[*] INITIATING TELEMETRY STRIKE | CHUNK SIZE: {c_size}")
        
        execution_id = f"VFRAC_TELEMETRY_{c_size}_{int(time.time())}"
        auth_sk, _, auth_pub = generate_keypair()
        holder_id = "EARTH_TELEMETRY_WORKER"
        epoch = 1

        status, _ = http_post(gate_url, {"action": "register_genesis", "execution_id": execution_id, "epoch": epoch, "holder": holder_id, "pub_key": auth_pub})
        if status != 200:
            print("[!] Genesis Failed.")
            continue

        applied_total = 0
        t0 = time.time()
        
        chunk_telemetry = []

        for chunk_start in range(0, batch_size, c_size):
            chunk_end = min(chunk_start + c_size, batch_size)
            batch_reqs = []
            
            for i in range(chunk_start, chunk_end):
                op_id = f"OP_TEL_{i:06d}"
                req = RecursiveConsequenceRequest(
                    execution_id=execution_id, epoch=epoch, holder_id=holder_id, operation_id=op_id,
                    target_resource="RES_A", signing_key_public=auth_pub, state_root="ROOT",
                    evidence_head="HEAD", payload_digest=f"dig_{i}", delegation_chain=[]
                )
                req.signature = sign_bytes(auth_sk, req.canonical_bytes())
                batch_reqs.append(req.to_dict())

            status, val_resp = http_post(gate_url, {"action": "validate_batch_consequences", "requests": batch_reqs})
            if status == 200:
                http_post(sink_url, {"action": "apply_batch_permits", "permits": val_resp.get("permits", [])})
            
            ws, priv, pf = get_mem()
            gc_stats = gc.get_count()
            
            chunk_telemetry.append({
                "ops_processed": chunk_end,
                "working_set_mb": ws / (1024*1024),
                "private_bytes_mb": priv / (1024*1024),
                "page_faults": pf,
                "gc_counts": gc_stats
            })
            
            if chunk_end % 20000 == 0:
                print(f"  -> Traversed {chunk_end}/{batch_size} ops | WS: {ws / (1024*1024):.1f}MB | Priv: {priv / (1024*1024):.1f}MB")

        t1 = time.time()
        mars_state = fetch_mars_state(sink_url)
        
        report.append({
            "chunk_size": c_size,
            "elapsed_s": t1 - t0,
            "throughput": batch_size / (t1 - t0),
            "telemetry": chunk_telemetry,
            "mars_independent_state": mars_state
        })
        
        print(f"[*] RUN COMPLETE | Throughput: {batch_size / (t1 - t0):.1f} ops/s")
        print(f"[*] MARS READBACK: Counter = {mars_state.get('counter')}, Last Op = {mars_state.get('last_op')}")
        time.sleep(2) # Cooldown

    with open("C:\\Users\\antho\\vchip\\telemetry_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    execute_telemetry_strike("http://192.168.2.28:8020", "http://192.168.2.28:8040")
