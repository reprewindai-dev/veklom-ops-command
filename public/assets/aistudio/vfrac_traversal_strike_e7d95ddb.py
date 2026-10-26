import sys, json, time, urllib.request

urllib.request.getproxies = lambda: {}

from vchip_core import (
    generate_keypair, sign_bytes, ALLOW
)
from vfrac_recursive_core import RecursiveConsequenceRequest

def http_post(url, payload, timeout=10.0):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return 500, {"error": str(e)}

def execute_bounded_traversal(gate_url, sink_url, batch_size=100000):
    print(f"================================================================")
    print(f"[*] EXECUTING BOUNDED-RESIDENCY TRANSVERSAL STRIKE")
    print(f"[*] Target Gate: {gate_url}")
    print(f"[*] Target Sink: {sink_url}")
    print(f"[*] Logical State (Batch Size): {batch_size}")
    print(f"================================================================")

    execution_id = f"VFRAC_BOUNDED_STRIKE_{int(time.time())}"
    auth_sk, _, auth_pub = generate_keypair()
    holder_id = "EARTH_BOUNDED_WORKER"
    epoch = 1

    print(f"[*] Registering Genesis State... Execution ID: {execution_id}")
    gen_payload = {
        "action": "register_genesis",
        "execution_id": execution_id,
        "epoch": epoch,
        "holder": holder_id,
        "pub_key": auth_pub
    }
    status, _ = http_post(gate_url, gen_payload)
    if status != 200:
        print("[!] Genesis Registration Failed.")
        return

    chunk_size = 10000
    applied_total = 0
    t0 = time.time()
    
    print(f"[*] Commencing Bounded Transversal Strike (Chunk Size: {chunk_size})")

    for chunk_start in range(0, batch_size, chunk_size):
        chunk_end = min(chunk_start + chunk_size, batch_size)
        batch_reqs = []
        
        # 1. Generate Chunk
        for i in range(chunk_start, chunk_end):
            op_id = f"OP_TRAV_{i:06d}"
            req = RecursiveConsequenceRequest(
                execution_id=execution_id, epoch=epoch, holder_id=holder_id, operation_id=op_id,
                target_resource="RES_A", signing_key_public=auth_pub, state_root="ROOT",
                evidence_head="HEAD", payload_digest=f"dig_{i}", delegation_chain=[]
            )
            req.signature = sign_bytes(auth_sk, req.canonical_bytes())
            batch_reqs.append(req.to_dict())

        # 2. Transmit Chunk to Gate
        val_payload = {"action": "validate_batch_consequences", "requests": batch_reqs}
        status, val_resp = http_post(gate_url, val_payload, timeout=60.0)
        
        if status != 200:
            print(f"[!] Gate Rejected Chunk {chunk_start}: {val_resp}")
            return
            
        chunk_permits = val_resp.get("permits", [])
        
        # 3. Transmit Permits to Sink
        sink_payload = {"action": "apply_batch_permits", "permits": chunk_permits}
        status, sink_resp = http_post(sink_url, sink_payload, timeout=60.0)
        
        if status != 200:
            print(f"[!] Sink Rejected Chunk {chunk_start}: {sink_resp}")
            return
            
        applied_total += sink_resp.get("applied_count", 0)
        
        if (chunk_end) % 20000 == 0 or chunk_end == batch_size:
            print(f"  -> Traversed {chunk_end}/{batch_size} ops | Sink Applied: {applied_total} | Resident Working Set GC'd")

    t1 = time.time()
    print(f"================================================================")
    print(f"[*] BOUNDED TRANSVERSAL STRIKE COMPLETE")
    print(f"[*] Total Logical State Processed: {batch_size}")
    print(f"[*] Max Resident Working Set: ~{chunk_size} operations")
    print(f"[*] Elapsed Time: {t1 - t0:.2f}s")
    print(f"[*] Average Throughput: {batch_size / (t1 - t0):.1f} ops/s")
    print(f"================================================================")

if __name__ == "__main__":
    gate = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.2.28:8020"
    sink = sys.argv[2] if len(sys.argv) > 2 else "http://192.168.2.28:8040"
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
    execute_bounded_traversal(gate, sink, size)


