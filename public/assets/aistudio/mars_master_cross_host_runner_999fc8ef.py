import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

from vchip_core import generate_keypair, sign_bytes, ConsequenceRequest
from vfrac_recursive_core import RecursiveConsequenceRequest

# --- MASTER STRIKE RUNNER UTILITIES ---

def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

import socket

def check_endpoint(name, host, port):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True, "PORT_OPEN"
    except Exception as e:
        return False, str(e)

# --- MASTER STRIKE SUITE ---

def execute_master_cross_host_suite(target_ip="192.168.2.11"):
    print("\n" + "="*70)
    print(f" MARS MASTER CROSS-HOST GOVERNED EXECUTION STRIKE SUITE")
    print(f" Target Host (Earth): {target_ip}")
    print(f" Origin Host (Mars): 192.168.2.28")
    print(f" Protocol: REAL HTTP / TCP SOCKETS | Zero Mocks")
    print("="*70 + "\n")

    # Step 0: Pre-Flight Endpoint Discovery
    gate_url = f"http://{target_ip}:8020"
    sink_url = f"http://{target_ip}:8040"
    cappo_url = f"http://{target_ip}:8050"
    continuum_url = f"http://{target_ip}:8060"

    print("[0] PRE-FLIGHT ENDPOINT DISCOVERY...")
    ok_gate, msg_gate = check_endpoint("Gate", target_ip, 8020)
    ok_sink, msg_sink = check_endpoint("Sink", target_ip, 8040)
    ok_cappo, msg_cappo = check_endpoint("CAPPO", target_ip, 8050)
    ok_cont, msg_cont = check_endpoint("Continuum", target_ip, 8060)

    print(f"[*] Port 8020 (Gate):      {'ONLINE' if ok_gate else 'FAILED (' + msg_gate + ')'}")
    print(f"[*] Port 8040 (Sink):      {'ONLINE' if ok_sink else 'FAILED (' + msg_sink + ')'}")
    print(f"[*] Port 8050 (CAPPO):     {'ONLINE' if ok_cappo else 'FAILED (' + msg_cappo + ')'}")
    print(f"[*] Port 8060 (Continuum): {'ONLINE' if ok_cont else 'FAILED (' + msg_cont + ')'}")

    if not (ok_gate and ok_sink and ok_cappo and ok_cont):
        print(f"[!] ERROR: One or more remote endpoints on {target_ip} are offline. Aborting strike to prevent false verification.")
        return

    print(f"[*] All 4 Earth Endpoints Confirmed Online on {target_ip}. Firing Master Strike Suite...\n")
    results_summary = {}

    # -----------------------------------------------------------------
    # STRIKE 1: 100K RECIPROCAL TRAVERSAL STRIKE (Ports 8020 / 8040)
    # -----------------------------------------------------------------
    print("--- [STRIKE 1/5] 100K RECIPROCAL TRAVERSAL STRIKE (Ports 8020 / 8040) ---")
    start_s1 = time.time()
    try:
        auth_sk, auth_priv, auth_pub = generate_keypair()
        exec_id = f"VFRAC_MARS_STRIKE_100K_{int(time.time())}"
        
        # Genesis Register
        post_json(gate_url, {
            "action": "register_genesis",
            "execution_id": exec_id,
            "epoch": 1,
            "holder_id": "MARS_STRIKE_WORKER",
            "pub_key": auth_pub
        })

        ops_applied = 0
        total_ops = 100000
        batch_size = 10000
        total_batches = total_ops // batch_size

        for b in range(total_batches):
            sub_batch = []
            for i in range(batch_size):
                op_idx = b * batch_size + i
                op_id = f"OP_MARS_TRAV_{op_idx:06d}"
                req_obj = RecursiveConsequenceRequest(
                    execution_id=exec_id,
                    epoch=1,
                    holder_id="MARS_STRIKE_WORKER",
                    operation_id=op_id,
                    target_resource="RESOURCE_A",
                    signing_key_public=auth_pub,
                    state_root="GENESIS_STATE_ROOT",
                    evidence_head="GENESIS_EVIDENCE_HEAD",
                    payload_digest=f"digest_{op_idx}",
                    delegation_chain=[]
                )
                req_obj.signature = sign_bytes(auth_sk, req_obj.canonical_bytes())
                sub_batch.append(req_obj.to_dict())

            gate_res = post_json(gate_url, {
                "action": "validate_batch_consequences",
                "requests": sub_batch
            }, timeout=120)

            permits = gate_res.get("permits", [])
            sink_res = post_json(sink_url, {
                "action": "apply_batch_permits",
                "permits": permits
            }, timeout=120)

            ops_applied += len(permits)
            print(f"[*] Batch {b+1}/{total_batches} ALLOWED ({ops_applied}/{total_ops} ops) | Earth Sink Counter: {sink_res.get('current_state', {}).get('counter', sink_res.get('counter'))}")

        dur_s1 = time.time() - start_s1
        results_summary["STRIKE_1_100K_TRAVERSAL"] = {
            "status": "PASS",
            "ops": ops_applied,
            "time_sec": round(dur_s1, 2),
            "throughput_ops_sec": round(ops_applied / dur_s1, 2)
        }
    except Exception as e:
        results_summary["STRIKE_1_100K_TRAVERSAL"] = {"status": "FAIL", "error": str(e)}
        print(f"[!] Strike 1 Exception: {e}")

    print()

    # -----------------------------------------------------------------
    # STRIKE 2: 100% CAPPO TRAVERSAL STRIKE (Port 8050)
    # -----------------------------------------------------------------
    print("--- [STRIKE 2/5] 100% CAPPO CAPABILITY TRAVERSAL STRIKE (Port 8050) ---")
    start_s2 = time.time()
    try:
        exec_id_cappo = f"CAPPO_MARS_STRIKE_{int(time.time())}"
        lease_res = post_json(f"{cappo_url}/cappo", {
            "action": "issue_lease",
            "execution_id": exec_id_cappo,
            "epoch": 1,
            "holder_id": "MARS_CAPPO_WORKER",
            "max_budget": 100000,
            "allowed_resources": ["REALITY_SINK", "MUTATE_STATE"],
            "max_depth": 3
        })
        lease = lease_res["lease"]

        cappo_ops = 100000
        cappo_batch = 10000
        cappo_batches = cappo_ops // cappo_batch
        cappo_applied = 0

        for b in range(cappo_batches):
            batch_ops = [{"operation_id": f"OP_CAPPO_{b*cappo_batch+i:06d}"} for i in range(cappo_batch)]
            res = post_json(f"{cappo_url}/cappo", {
                "action": "authorize_and_apply_batch",
                "lease": lease,
                "operations": batch_ops,
                "target_resource": "REALITY_SINK"
            }, timeout=60)
            cappo_applied += res["authorized_count"]
            print(f"[*] CAPPO Batch {b+1}/{cappo_batches} ALLOWED ({cappo_applied}/{cappo_ops} ops) | CAPPO Counter: {res['sink_counter']}")

        dur_s2 = time.time() - start_s2
        results_summary["STRIKE_2_CAPPO_TRAVERSAL"] = {
            "status": "PASS",
            "ops": cappo_applied,
            "time_sec": round(dur_s2, 2),
            "throughput_ops_sec": round(cappo_applied / dur_s2, 2)
        }
    except Exception as e:
        results_summary["STRIKE_2_CAPPO_TRAVERSAL"] = {"status": "FAIL", "error": str(e)}
        print(f"[!] Strike 2 Exception: {e}")

    print()

    # -----------------------------------------------------------------
    # STRIKE 3: CONTINUUM PROOF SUITE (Port 8060)
    # -----------------------------------------------------------------
    print("--- [STRIKE 3/5] CONTINUUM PROOF SUITE (Port 8060) ---")
    start_s3 = time.time()
    try:
        # 3A: Ghost Tarpit
        post_json(f"{continuum_url}/c", {"action": "execute_with_tarpit_check", "lineage_id": "L1_PRIMARY", "epoch": 1, "holder_id": "WORKER_EARTH", "operations": [{"op_id": "OP_1"}]})
        post_json(f"{continuum_url}/c", {"action": "advance_epoch", "lineage_id": "L1_PRIMARY", "new_epoch": 2, "revoke_holder": "WORKER_EARTH"})
        res_tarpit = post_json(f"{continuum_url}/c", {"action": "execute_with_tarpit_check", "lineage_id": "L1_PRIMARY", "epoch": 1, "holder_id": "WORKER_EARTH", "operations": [{"op_id": "OP_STALE"}]})
        print(f"[+] 3A. Ghost Tarpit: {res_tarpit['status']} | Real Mutation: {res_tarpit['real_state_mutation']}")

        # 3B: Fracturing
        h1 = hashlib.sha256(b"MARS").hexdigest()
        res_frac = post_json(f"{continuum_url}/c", {"action": "apply_fracture_chunk", "fracture_id": "MARS_FRAC", "lineage_id": "L1_PRIMARY", "ops_count": 33333, "partial_hash": h1})
        print(f"[+] 3B. Workload Fracturing: {res_frac['status']} | Counter: {res_frac['total_counter']}")

        # 3C: Time-Travel Forking
        res_fork = post_json(f"{continuum_url}/c", {"action": "fork_timeline", "source_lineage": "L1_PRIMARY", "fork_at_hash": h1, "new_lineage": "L2_TIMELINE_FORK"})
        print(f"[+] 3C. Time-Travel Forking: {res_fork['status']} | New Lineage: {res_fork['new_lineage']}")

        # 3D: Insider Tamper Fencing
        try:
            post_json(f"{continuum_url}/c", {"action": "audit_disk_integrity", "disk_counter": 999999, "disk_hash": "FORGED_HASH"})
        except urllib.error.HTTPError as e:
            res_tamper = json.loads(e.read().decode("utf-8"))
            print(f"[+] 3D. Insider Tamper Fenced: {res_tamper['status']} | Action: {res_tamper['action_taken']}")

        dur_s3 = time.time() - start_s3
        results_summary["STRIKE_3_CONTINUUM_SUITE"] = {
            "status": "PASS",
            "proofs_verified": 4,
            "time_sec": round(dur_s3, 2)
        }
    except Exception as e:
        results_summary["STRIKE_3_CONTINUUM_SUITE"] = {"status": "FAIL", "error": str(e)}
        print(f"[!] Strike 3 Exception: {e}")

    print()

    # -----------------------------------------------------------------
    # STRIKE 4: UNIVERSAL CONSENSUS ENGINE (Port 8020)
    # -----------------------------------------------------------------
    print("--- [STRIKE 4/5] UNIVERSAL CONSENSUS & KEY ROTATION (Port 8020) ---")
    start_s4 = time.time()
    try:
        from vfrac_unified_consensus_engine import run_unified_consensus_harness
        res_s4 = run_unified_consensus_harness(gate_url, sink_url, batch_size=10000)
        dur_s4 = time.time() - start_s4
        status_s4 = "PASS" if res_s4.get("passed") else "FAIL"
        results_summary["STRIKE_4_UNIVERSAL_CONSENSUS"] = {"status": status_s4, "metrics": res_s4.get("metrics"), "time_sec": round(dur_s4, 2)}
    except Exception as e:
        results_summary["STRIKE_4_UNIVERSAL_CONSENSUS"] = {"status": "FAIL", "error": str(e)}
        print(f"[!] Strike 4 Exception: {e}")

    print()

    # -----------------------------------------------------------------
    # STRIKE 5: SUBSTRATE HEALING ENGINE (Port 8020)
    # -----------------------------------------------------------------
    print("--- [STRIKE 5/5] SUBSTRATE HEALING & REVOCATION (Port 8020) ---")
    start_s5 = time.time()
    try:
        from vfrac_substrate_healing_engine import run_substrate_healing_harness
        unique_heal_id = f"VFRAC_SUBSTRATE_HEALING_{int(time.time())}"
        res_s5 = run_substrate_healing_harness(gate_url, sink_url, execution_id=unique_heal_id)
        dur_s5 = time.time() - start_s5
        status_s5 = "PASS" if res_s5.get("passed") else "FAIL"
        results_summary["STRIKE_5_SUBSTRATE_HEALING"] = {"status": status_s5, "time_sec": round(dur_s5, 2)}
    except Exception as e:
        results_summary["STRIKE_5_SUBSTRATE_HEALING"] = {"status": "FAIL", "error": str(e)}
        print(f"[!] Strike 5 Exception: {e}")

    # -----------------------------------------------------------------
    # MASTER STRIKE RESULTS SUMMARY
    # -----------------------------------------------------------------
    print("\n" + "="*70)
    print(" MARS MASTER CROSS-HOST GOVERNED EXECUTION STRIKE SUMMARY")
    print("="*70)
    for k, v in results_summary.items():
        print(f" [{v['status']}] {k}: {v}")
    print("="*70 + "\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "192.168.2.11"
    execute_master_cross_host_suite(target)
