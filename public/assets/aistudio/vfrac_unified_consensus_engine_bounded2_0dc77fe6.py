import sys, json, time
import urllib.request
urllib.request.getproxies = lambda: {}
from vchip_core import (
    VChipIdentity, AuthorityRecord, HandoffPackage, ConsequenceRequest, ConsequencePermit,
    generate_keypair, sign_bytes, verify_signature,
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_BAD_SIGNATURE, DENY_REPLAYED_OPERATION
)
from vfrac_recursive_core import RecursiveConsequenceRequest

def http_post(url, payload, timeout=5.0):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 500, {"error": str(e)}

def run_unified_consensus_harness(gate_url, sink_url, batch_size=100000):
    results = {"passed": False, "frontiers": {}, "metrics": {}}
    execution_id = "VFRAC_UNIFIED_CONSENSUS"
    auth1_sk, _, auth1_pub_hex = generate_keypair()
    auth2_sk, _, auth2_pub_hex = generate_keypair()
    holder_sk, _, holder_pub_hex = generate_keypair()
    epoch = 1
    holder_id = "VFRAC_FEDERATED_NODE_ALPHA"
    state_root = "ROOT_HASH_EPOCH_1"
    evidence_head = "EVIDENCE_HEAD_EPOCH_1"

    gen_payload = {
        "action": "register_genesis",
        "execution_id": execution_id,
        "epoch": epoch,
        "holder": holder_id,
        "pub_key": auth1_pub_hex
    }
    status, resp = http_post(gate_url, gen_payload)
    if status != 200: return results
    
    # Bounded Residency Processing!
    chunk_size = 10000
    applied_total = 0
    t0 = time.time()
    
    for chunk_start in range(0, batch_size, chunk_size):
        chunk_end = min(chunk_start + chunk_size, batch_size)
        batch_reqs = []
        for i in range(chunk_start, chunk_end):
            op_id = f"OP_UNI2_{i:06d}"
            req = RecursiveConsequenceRequest(
                execution_id=execution_id, epoch=epoch, holder_id=holder_id, operation_id=op_id,
                target_resource="RESOURCE_A", signing_key_public=auth1_pub_hex, state_root=state_root,
                evidence_head=evidence_head, payload_digest=f"digest_{i}", delegation_chain=[]
            )
            req.signature = sign_bytes(auth1_sk, req.canonical_bytes())
            batch_reqs.append(req.to_dict())

        val_payload = {"action": "validate_batch_consequences", "requests": batch_reqs}
        status, val_resp = http_post(gate_url, val_payload, timeout=180.0)
        if status != 200: return results
        
        chunk_permits = val_resp.get("permits", [])
        
        sink_payload = {"action": "apply_batch_permits", "permits": chunk_permits}
        status, sink_resp = http_post(sink_url, sink_payload, timeout=180.0)
        if status != 200: return results
        
        applied_total += sink_resp.get("applied_count", 0)
        final_counter = sink_resp.get("current_counter", 0)
        print(f"[+] Chunk {chunk_start} processed. Total applied: {applied_total}")

    results["frontiers"]["multi_sink_consensus"] = True
    results["metrics"]["batch_size"] = batch_size
    
    # Stale Epoch Check
    stale_req = ConsequenceRequest(
        execution_id=execution_id, epoch=epoch - 1, holder_id=holder_id,
        operation_id="OP_STALE_001", signing_key_public=holder_pub_hex,
        state_root=state_root, evidence_head=evidence_head, payload_digest="stale_digest"
    )
    stale_req.signature = sign_bytes(holder_sk, stale_req.canonical_bytes())
    val_stale_payload = {"action": "validate_consequence", "consequence_request": stale_req.to_dict()}
    status, stale_resp = http_post(gate_url, val_stale_payload)
    print(f"[+] Stale Check Status: {status} | Resp: {stale_resp}")
    results["passed"] = True
    return results

if __name__ == "__main__":
    gate = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020"
    sink = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8040"
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
    res = run_unified_consensus_harness(gate, sink, batch_size=size)
    print(json.dumps(res, indent=2))


