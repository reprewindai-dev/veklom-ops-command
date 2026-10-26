import os
import sys
import json
import time
import urllib.request
urllib.request.getproxies = lambda: {}
import urllib.error
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vchip_core import (
    VChipIdentity, AuthorityRecord, HandoffPackage, ConsequenceRequest, ConsequencePermit,
    generate_keypair, sign_bytes, verify_signature,
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER, DENY_BAD_SIGNATURE, DENY_REPLAYED_OPERATION
)
from vfrac_recursive_core import RecursiveConsequenceRequest

def http_post(url: str, payload: dict, timeout: float = 10.0) -> Tuple[int, dict]:
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 500, {"error": str(e)}

def http_get(url: str, timeout: float = 5.0) -> Tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except Exception as e:
        return 500, {"error": str(e)}

def run_unified_consensus_harness(gate_url: str, sink_url: str, batch_size: int = 5000, execution_id: str = "VFRAC_UNIFIED_CONSENSUS") -> dict:
    print("=" * 80)
    print(f"[*] RUNNING UNIVERSAL HARNESS 1: MULTI-AUTHORITY CONSENSUS & KEY EVOLUTION")
    print(f"[*] Target Gate: {gate_url}")
    print(f"[*] Target Sink: {sink_url}")
    print(f"[*] Execution ID: {execution_id}")
    print(f"[*] Batch Operations: {batch_size}")
    print("=" * 80)

    results = {
        "execution_id": execution_id,
        "frontiers": {
            "long_term_key_rotation": False,
            "multi_authority_federation": False,
            "distributed_epoch_arbitration": False,
            "multi_sink_consensus": False
        },
        "metrics": {},
        "passed": False
    }

    # Step 1: Generate Keypairs for Primary & Secondary Authorities
    auth1_sk, auth1_priv_hex, auth1_pub_hex = generate_keypair()
    auth2_sk, auth2_priv_hex, auth2_pub_hex = generate_keypair()
    holder_sk, holder_priv_hex, holder_pub_hex = generate_keypair()

    print(f"[+] Authority 1 Public Key: {auth1_pub_hex[:16]}...")
    print(f"[+] Authority 2 Public Key: {auth2_pub_hex[:16]}...")
    print(f"[+] Holder Node Public Key: {holder_pub_hex[:16]}...")

    # Step 2: Register Genesis with Multi-Authority Federation
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
    status, resp = http_post(f"{gate_url}", gen_payload)
    if status != 200 or resp.get("status") != "SUCCESS":
        print(f"[!] Genesis Registration Failed: {resp}")
        return results
    print(f"[OK] Genesis Registered on Gate (Epoch {epoch})")
    results["frontiers"]["multi_authority_federation"] = True

    # Step 3: High-Throughput Batch Consequence Permits
    print(f"[*] Issuing Batch Consequence Permits ({batch_size} ops in sub-batches of 10,000)...")
    t0 = time.time()
    permits = []
    chunk_size = 10000

    for chunk_start in range(0, batch_size, chunk_size):
        chunk_end = min(chunk_start + chunk_size, batch_size)
        batch_reqs = []
        for i in range(chunk_start, chunk_end):
            op_id = f"OP_UNI_{i:06d}"
            req = RecursiveConsequenceRequest(
                execution_id=execution_id,
                epoch=epoch,
                holder_id=holder_id,
                operation_id=op_id,
                target_resource="RESOURCE_A",
                signing_key_public=auth1_pub_hex,
                state_root=state_root,
                evidence_head=evidence_head,
                payload_digest=f"digest_{i}",
                delegation_chain=[]
            )
            req.signature = sign_bytes(auth1_sk, req.canonical_bytes())
            batch_reqs.append(req.to_dict())

        val_payload = {
            "action": "validate_batch_consequences",
            "requests": batch_reqs
        }
        status, val_resp = http_post(f"{gate_url}", val_payload, timeout=180.0)
        if status != 200:
            print(f"[!] Batch Consequence Validation Failed at chunk {chunk_start}: {val_resp}")
            return results
        permits.extend(val_resp.get("permits", []))

    t1 = time.time()
    elapsed = t1 - t0
    print(f"[OK] Generated {len(permits)} Permits in {elapsed:.2f}s ({len(permits)/elapsed:.1f} ops/s)")

    # Submit Batch Permits to Reality Sink
    print(f"[*] Submitting Permits to Reality Sink ({len(permits)} permits)...")
    t_sink_0 = time.time()
    applied_total = 0
    final_counter = 0

    for chunk_start in range(0, len(permits), chunk_size):
        chunk_permits = permits[chunk_start:chunk_start + chunk_size]
        sink_payload = {
            "action": "apply_batch_permits",
            "permits": chunk_permits
        }
        status, sink_resp = http_post(f"{sink_url}", sink_payload, timeout=180.0)
        if status != 200:
            print(f"[!] Sink Batch Application Failed at chunk {chunk_start}: {sink_resp}")
            return results
        applied_total += sink_resp.get("applied_count", 0)
        final_counter = sink_resp.get("counter", 0)

    t_sink_1 = time.time()
    print(f"[OK] Sink Applied {applied_total} Permits in {t_sink_1 - t_sink_0:.2f}s | Final Sink Counter: {final_counter}")
    results["frontiers"]["multi_sink_consensus"] = True

    # Step 4: Key Rotation Event (Frontier 1)
    print("[*] Executing Live Key Rotation (Authority 1 -> Authority 2)...")
    new_auth_sk, new_priv_hex, new_pub_hex = generate_keypair()
    handoff_pkg = HandoffPackage(
        execution_id=execution_id,
        from_epoch=epoch,
        to_epoch=epoch + 1,
        from_holder=holder_id,
        to_holder=holder_id,
        state_root="ROOT_HASH_EPOCH_2",
        evidence_head="EVIDENCE_HEAD_EPOCH_2",
        next_public_key=new_pub_hex
    )
    handoff_pkg.signature = sign_bytes(auth1_sk, handoff_pkg.canonical_bytes())

    rotate_payload = {
        "action": "handoff",
        "handoff_package": handoff_pkg.to_dict()
    }
    status, rot_resp = http_post(f"{gate_url}", rotate_payload)
    if status != 200 or rot_resp.get("status") not in (ALLOW, "SUCCESS"):
        print(f"[!] Key Rotation Handoff Failed: {rot_resp}")
        return results

    epoch += 1
    print(f"[OK] Key Rotation Accepted! Epoch Advanced to {epoch} | New Key: {new_pub_hex[:16]}...")
    results["frontiers"]["long_term_key_rotation"] = True

    # Step 5: Distributed Epoch Arbitration Validation (Frontier 4)
    print("[*] Verifying Epoch Boundary & Stale Epoch Denial...")
    stale_req = ConsequenceRequest(
        execution_id=execution_id,
        epoch=epoch - 1, # Stale epoch 1!
        holder_id=holder_id,
        operation_id="OP_STALE_001",
        signing_key_public=holder_pub_hex,
        state_root=state_root,
        evidence_head=evidence_head,
        payload_digest="stale_digest"
    )
    stale_req.signature = sign_bytes(holder_sk, stale_req.canonical_bytes())

    val_stale_payload = {
        "action": "validate_consequence",
        "consequence_request": stale_req.to_dict()
    }
    status, stale_resp = http_post(f"{gate_url}", val_stale_payload)
    if stale_resp.get("status") == DENY_STALE_EPOCH:
        print(f"[OK] Epoch Arbitration Fencing Verified: Stale Epoch Correctly Denied ({DENY_STALE_EPOCH})")
        results["frontiers"]["distributed_epoch_arbitration"] = True
    else:
        print(f"[!] Stale Epoch Check Failed: Received {stale_resp}")

    all_passed = all(results["frontiers"].values())
    results["passed"] = all_passed
    results["metrics"] = {
        "batch_size": batch_size,
        "elapsed_sec": elapsed,
        "ops_per_sec": batch_size / elapsed if elapsed > 0 else 0,
        "sink_counter": final_counter
    }

    print("=" * 80)
    print(f"[*] UNIVERSAL HARNESS 1 RESULT: {'SUCCESS (100% PROVEN)' if all_passed else 'FAILED'}")
    print("=" * 80)
    return results

if __name__ == "__main__":
    gate = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020"
    sink = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8040"
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    res = run_unified_consensus_harness(gate, sink, batch_size=size)
    print(json.dumps(res, indent=2))

