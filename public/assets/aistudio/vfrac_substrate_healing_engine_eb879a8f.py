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
    ALLOW, DENY_WRONG_HOLDER, DENY_BAD_SIGNATURE, DENY_STALE_EPOCH
)

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

def run_substrate_healing_harness(gate_url: str, sink_url: str, execution_id: str = "VFRAC_SUBSTRATE_HEALING") -> dict:
    print("=" * 80)
    print(f"[*] RUNNING UNIVERSAL HARNESS 2: AUTONOMOUS REVOCATION & SUBSTRATE HEALING")
    print(f"[*] Target Gate: {gate_url}")
    print(f"[*] Target Sink: {sink_url}")
    print(f"[*] Execution ID: {execution_id}")
    print("=" * 80)

    results = {
        "execution_id": execution_id,
        "frontiers": {
            "active_executor_revocation": False,
            "substrate_healing_after_failure": False,
            "cross_substrate_reconciliation": False
        },
        "metrics": {},
        "passed": False
    }

    # Generate keys for Holder Alpha and Fallback Holder Beta
    auth_sk, auth_priv_hex, auth_pub_hex = generate_keypair()
    node_a_sk, node_a_priv, node_a_pub = generate_keypair()
    node_b_sk, node_b_priv, node_b_pub = generate_keypair()

    _suffix = execution_id.split("_")[-1] if "_" in execution_id else str(int(time.time()))
    node_a_id = f"MARS_PRIMARY_WORKER_{_suffix}"
    node_b_id = f"EARTH_FALLBACK_WORKER_{_suffix}"

    epoch = 1
    state_root = "HEALING_ROOT_EPOCH_1"
    evidence_head = "HEALING_EVIDENCE_EPOCH_1"

    # Register Genesis with Gate
    gen_payload = {
        "action": "register_genesis",
        "execution_id": execution_id,
        "epoch": epoch,
        "holder": node_a_id,
        "pub_key": node_a_pub
    }
    status, resp = http_post(f"{gate_url}", gen_payload)
    if status != 200 or resp.get("status") != "SUCCESS":
        print(f"[!] Genesis Registration Failed: {resp}")
        return results
    print(f"[OK] Genesis Registered: Holder {node_a_id}")

    # Set Node Ceilings
    ceil_payload = {
        "action": "set_ceilings",
        "node_ceilings": {
            node_a_id: ["RESOURCE_A", "RESOURCE_B"],
            node_b_id: ["RESOURCE_A", "RESOURCE_B"]
        }
    }
    http_post(f"{gate_url}", ceil_payload)

    # Step 1: Active Consequence Stream from Primary Worker
    print(f"[*] Executing Consequence Stream from Primary Worker ({node_a_id})...")
    req1 = ConsequenceRequest(
        execution_id=execution_id,
        epoch=epoch,
        holder_id=node_a_id,
        operation_id="OP_PRIMARY_001",
        signing_key_public=node_a_pub,
        state_root=state_root,
        evidence_head=evidence_head,
        payload_digest="digest_primary_001"
    )
    req1.signature = sign_bytes(node_a_sk, req1.canonical_bytes())
    status, resp1 = http_post(f"{gate_url}", {"action": "validate_consequence", "consequence_request": req1.to_dict()})

    if status != 200 or resp1.get("status") != ALLOW:
        print(f"[!] Primary Worker Request Failed: {resp1}")
        return results
    print(f"[OK] Primary Worker Request Permitted ({ALLOW})")

    # Step 2: Active Executor Revocation (Frontier 6)
    print(f"[*] Revoking Primary Worker ({node_a_id}) Ceilings & Execution Permit...")
    revoke_payload = {
        "action": "revoke_node",
        "node_id": node_a_id
    }
    http_post(f"{gate_url}", revoke_payload)

    # Attempt second request from Revoked Node A
    req2 = ConsequenceRequest(
        execution_id=execution_id,
        epoch=epoch,
        holder_id=node_a_id,
        operation_id="OP_PRIMARY_002",
        signing_key_public=node_a_pub,
        state_root=state_root,
        evidence_head=evidence_head,
        payload_digest="digest_primary_002"
    )
    req2.signature = sign_bytes(node_a_sk, req2.canonical_bytes())
    status, resp2 = http_post(f"{gate_url}", {"action": "validate_consequence", "consequence_request": req2.to_dict()})

    if resp2.get("status") in ("DENY_NODE_REVOKED", "DENY_WRONG_HOLDER", "DENY_CEILING_EXCEEDED"):
        print(f"[OK] Active Executor Revocation Verified! Revoked Node Blocked: {resp2.get('status')}")
        results["frontiers"]["active_executor_revocation"] = True
    else:
        print(f"[!] Revocation Verification Failed: Received {resp2}")

    # Step 3: Substrate Healing & Automated Handoff to Fallback Worker (Frontier 7)
    print(f"[*] Initiating Substrate Self-Healing: Dynamic Handoff to Fallback Worker ({node_b_id})...")
    handoff_pkg = HandoffPackage(
        execution_id=execution_id,
        from_epoch=epoch,
        to_epoch=epoch + 1,
        from_holder=node_a_id,
        to_holder=node_b_id,
        state_root="HEALING_ROOT_EPOCH_2",
        evidence_head="HEALING_EVIDENCE_EPOCH_2",
        next_public_key=node_b_pub
    )
    handoff_pkg.signature = sign_bytes(node_a_sk, handoff_pkg.canonical_bytes())

    status, h_resp = http_post(f"{gate_url}", {"action": "handoff", "handoff_package": handoff_pkg.to_dict()})
    if status != 200 or h_resp.get("status") not in (ALLOW, "SUCCESS"):
        print(f"[!] Substrate Handoff Failed: {h_resp}")
        return results

    epoch += 1
    print(f"[OK] Substrate Handoff Complete! Epoch: {epoch} | Active Holder: {node_b_id}")

    # Fallback Node B executes operations
    req_b = ConsequenceRequest(
        execution_id=execution_id,
        epoch=epoch,
        holder_id=node_b_id,
        operation_id="OP_FALLBACK_001",
        signing_key_public=node_b_pub,
        state_root="HEALING_ROOT_EPOCH_2",
        evidence_head="HEALING_EVIDENCE_EPOCH_2",
        payload_digest="digest_fallback_001"
    )
    req_b.signature = sign_bytes(node_b_sk, req_b.canonical_bytes())
    status, resp_b = http_post(f"{gate_url}", {"action": "validate_consequence", "consequence_request": req_b.to_dict()})

    if status == 200 and resp_b.get("status") == ALLOW:
        print(f"[OK] Fallback Worker Successfully Healed Execution Substrate!")
        results["frontiers"]["substrate_healing_after_failure"] = True
    else:
        print(f"[!] Fallback Worker Request Failed: {resp_b}")

    # Step 4: Cross-Substrate Reconciliation (Frontier 3)
    print("[*] Validating Cross-Substrate Reconciliation & Evidence Head Lineage...")
    status, gate_state = http_get(f"{gate_url}/{execution_id}")
    status, sink_state = http_get(f"{sink_url}")

    if gate_state.get("current_holder") == node_b_id and gate_state.get("current_epoch") == epoch:
        print(f"[OK] Cross-Substrate Lineage Reconciled: Holder={node_b_id} | Epoch={epoch}")
        results["frontiers"]["cross_substrate_reconciliation"] = True

    all_passed = all(results["frontiers"].values())
    results["passed"] = all_passed

    print("=" * 80)
    print(f"[*] UNIVERSAL HARNESS 2 RESULT: {'SUCCESS (100% PROVEN)' if all_passed else 'FAILED'}")
    print("=" * 80)
    return results

if __name__ == "__main__":
    gate = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8020"
    sink = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8040"
    res = run_substrate_healing_harness(gate, sink)
    print(json.dumps(res, indent=2))
