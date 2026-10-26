import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

from vchip_core import (
    generate_keypair, sign_bytes, ConsequenceRequest, HandoffPackage,
    ALLOW, DENY_STALE_EPOCH, DENY_WRONG_HOLDER
)

def http_post(url, payload, timeout=10.0):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"raw_error": e.read().decode("utf-8")}
    except Exception as e:
        return 0, {"error": str(e)}

def http_get(url, timeout=5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return 0, {"error": str(e)}

def execute_resurrection_strike(victim_host, striker_label, victim_label):
    gate_url = f"http://{victim_host}:8020"
    sink_url = f"http://{victim_host}:8040"

    print("="*75)
    print(f"[*] RESURRECTION ATTACK: {striker_label} -> {victim_label} ({victim_host})")
    print("="*75)

    unique_id = uuid.uuid4().hex[:8]
    execution_id = f"RESURRECT_{striker_label}_TO_{victim_label}_{int(time.time()*1000)}_{unique_id}"

    # Generate keys for legitimate primary and legitimate fallback
    sk_primary, _, pk_primary = generate_keypair()
    sk_fallback, _, pk_fallback = generate_keypair()

    primary_id = f"PRIMARY_{striker_label}_{unique_id}"
    fallback_id = f"FALLBACK_{victim_label}_{unique_id}"

    # Baseline Sink readback
    _, initial_sink = http_get(f"{sink_url}/status")
    initial_counter = initial_sink.get("counter", 0)
    print(f"[*] Baseline Sink Counter on {victim_label}: {initial_counter}")

    # Step 1: Genesis registration at Epoch 1
    print(f"[*] Step 1: Registering Genesis at Epoch 1 (Holder: {primary_id})...")
    status, reg_res = http_post(gate_url, {
        "action": "register_genesis",
        "execution_id": execution_id,
        "epoch": 1,
        "holder": primary_id,
        "pub_key": pk_primary
    })
    print(f"[OK] Genesis Registered: status={status}, response={reg_res}")

    # Step 2: Valid Epoch 1 operation committed
    print(f"[*] Step 2: Primary executes legitimate Epoch 1 operation...")
    req_ep1 = ConsequenceRequest(
        execution_id=execution_id,
        epoch=1,
        holder_id=primary_id,
        operation_id=f"OP_LEGIT_EP1_{unique_id}",
        signing_key_public=pk_primary,
        state_root=f"ROOT_EP1_{unique_id}",
        evidence_head=f"EVID_EP1_{unique_id}",
        payload_digest=f"digest_ep1_{unique_id}"
    )
    req_ep1.signature = sign_bytes(sk_primary, req_ep1.canonical_bytes())
    status, val_res = http_post(gate_url, {
        "action": "validate_consequence",
        "consequence_request": req_ep1.to_dict()
    })
    permit_ep1 = val_res.get("permit")
    print(f"[OK] Gate Issued Epoch 1 Permit: status={status}")

    # Commit permit to Sink
    status, sink_res = http_post(sink_url, {
        "action": "apply_permit",
        "permit": permit_ep1
    })
    print(f"[OK] Sink Committed Epoch 1 Consequence: status={status}, counter={sink_res.get('current_state', {}).get('counter')}")

    # Step 3: Legitimate Handoff to Epoch 2
    print(f"[*] Step 3: Commencing Legitimate Handoff to Fallback ({fallback_id}) at Epoch 2...")
    handoff_pkg = HandoffPackage(
        execution_id=execution_id,
        from_epoch=1,
        to_epoch=2,
        from_holder=primary_id,
        to_holder=fallback_id,
        state_root=f"ROOT_EP2_{unique_id}",
        evidence_head=f"EVID_EP2_{unique_id}",
        next_public_key=pk_fallback
    )
    handoff_pkg.signature = sign_bytes(sk_primary, handoff_pkg.canonical_bytes())
    status, h_res = http_post(gate_url, {
        "action": "handoff",
        "handoff_package": handoff_pkg.to_dict()
    })
    print(f"[OK] Handoff Accepted by Gate: status={status}, new_epoch={h_res.get('new_epoch')}")

    # Step 4: Fallback operates legitimately under Epoch 2
    print(f"[*] Step 4: Fallback executes legitimate Epoch 2 operation...")
    req_ep2 = ConsequenceRequest(
        execution_id=execution_id,
        epoch=2,
        holder_id=fallback_id,
        operation_id=f"OP_LEGIT_EP2_{unique_id}",
        signing_key_public=pk_fallback,
        state_root=f"ROOT_EP2_{unique_id}",
        evidence_head=f"EVID_EP2_{unique_id}",
        payload_digest=f"digest_ep2_{unique_id}"
    )
    req_ep2.signature = sign_bytes(sk_fallback, req_ep2.canonical_bytes())
    status, val_res_2 = http_post(gate_url, {
        "action": "validate_consequence",
        "consequence_request": req_ep2.to_dict()
    })
    permit_ep2 = val_res_2.get("permit")
    status, sink_res_2 = http_post(sink_url, {
        "action": "apply_permit",
        "permit": permit_ep2
    })
    post_handoff_counter = sink_res_2.get('current_state', {}).get('counter')
    print(f"[OK] Sink Committed Epoch 2 Consequence: status={status}, counter={post_handoff_counter}")

    # =========================================================================
    # STEP 5: THE HOSTILE RESURRECTION ATTACK
    # =========================================================================
    print("\n" + "!"*75)
    print(f"[!] INITIATING HOSTILE RESURRECTION ATTACK ON {victim_label}!")
    print(f"    Simulating zombie Primary Worker ({primary_id}) restored from disk snapshot")
    print(f"    Possessing authentic code, historical state, and authentic Epoch 1 key (sk_primary)")
    print(f"    Firing stale Epoch 1 mutations directly at {victim_label} Consequence Gate...")
    print("!"*75 + "\n")

    resurrection_ops = 5
    fenced_count = 0
    for i in range(resurrection_ops):
        zombie_op_id = f"ZOMBIE_MUTATION_{i}_{unique_id}"
        zombie_req = ConsequenceRequest(
            execution_id=execution_id,
            epoch=1,  # Stale Epoch 1!
            holder_id=primary_id,
            operation_id=zombie_op_id,
            signing_key_public=pk_primary,
            state_root=f"ROOT_EP1_{unique_id}",
            evidence_head=f"EVID_EP1_{unique_id}",
            payload_digest=f"zombie_digest_{i}"
        )
        zombie_req.signature = sign_bytes(sk_primary, zombie_req.canonical_bytes())

        status, attack_res = http_post(gate_url, {
            "action": "validate_consequence",
            "consequence_request": zombie_req.to_dict()
        })

        if status == 400 and attack_res.get("status") in (DENY_STALE_EPOCH, DENY_WRONG_HOLDER):
            fenced_count += 1
            print(f"[*] Zombie Op {i} [BLOCKED]: HTTP {status} | Denial: {attack_res.get('status')}")
        else:
            print(f"[!] Zombie Op {i} [BREACH!]: HTTP {status} | Response: {attack_res}")

    # Step 6: Independent Sink Readback
    print("\n" + "="*75)
    print(f"[*] INDEPENDENT AUDIT OF {victim_label} REALITY SINK POST-ATTACK")
    print("="*75)
    _, final_sink = http_get(f"{sink_url}/status")
    final_counter = final_sink.get("counter", 0)

    print(f"[*] Baseline Counter:     {initial_counter}")
    print(f"[*] Post-Handoff Counter: {post_handoff_counter}")
    print(f"[*] Final Sink Counter:   {final_counter}")

    if final_counter == post_handoff_counter and fenced_count == resurrection_ops:
        print(f"[+] VERDICT: 100% FALSIFICATION RESISTANCE PROVEN!")
        print(f"    All {resurrection_ops} resurrection attacks fenced strictly with DENY_STALE_EPOCH.")
        print(f"    Zero zombie mutations touched {victim_label} Reality Sink.")
        verdict = "PASS_FENCED"
    else:
        print(f"[!] VERDICT: FAILED - State was mutated or attacks were not completely fenced.")
        verdict = "FAIL_BREACH"

    print("="*75 + "\n")
    return verdict

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bidirectional Resurrection Falsification Test")
    parser.add_argument("--direction", choices=["mars_to_earth", "earth_to_mars"], default="mars_to_earth")
    args = parser.parse_args()

    if args.direction == "mars_to_earth":
        execute_resurrection_strike("192.168.2.11", "MARS", "EARTH")
    else:
        execute_resurrection_strike("192.168.2.28", "EARTH", "MARS")
