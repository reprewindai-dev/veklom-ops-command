import asyncio
import hashlib
import json
import struct
import sys
import time

try:
    import httpx
except ImportError:
    print("Missing httpx. Run: python -m pip install httpx")
    sys.exit(1)

MARS_IP = "192.168.2.28"
GATE_PORT = 8200
SINK_PORT = 8400

LINEAGE_ID = "STABLE_DATA_PLANE_V1"
EPOCH = 4
STEP = 245


async def tcp_check(label, host, port):
    print(f"[*] Checking {label}: {host}:{port}")

    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=3.0,
        )
        writer.close()
        await writer.wait_closed()
        print(f"[OK] {label} reachable")
        return True

    except Exception as exc:
        print(f"[FAIL] {label}: {type(exc).__name__}: {exc}")
        return False


def build_frame():
    run_id = f"EARTH_TO_MARS_SMOKE_{time.time_ns()}"
    timestamp_ns = time.time_ns()

    operation_id = hashlib.sha256(
        f"{run_id}:{LINEAGE_ID}:{EPOCH}:{STEP}".encode("utf-8")
    ).hexdigest()

    raw_manifest = f"{LINEAGE_ID}:{EPOCH}:{STEP}:{timestamp_ns}"

    signature_hex = hashlib.sha256(
        raw_manifest.encode("utf-8")
    ).hexdigest()

    manifest = {
        "run_id": run_id,
        "operation_id": operation_id,
        "lineage_id": LINEAGE_ID,
        "epoch": EPOCH,
        "step": STEP,
        "timestamp_ns": timestamp_ns,
        "signature_hex": signature_hex,
        "payload": f"SYNCHRONIZE_REALITY_STATE_STEP_{STEP}",
    }

    serialized = json.dumps(
        manifest,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    frame = struct.pack("!BI", 0x51, len(serialized)) + serialized

    return run_id, operation_id, manifest, frame


async def main():
    print("=" * 72)
    print("VEKLOM EARTH -> MARS SMOKE TEST")
    print("=" * 72)

    print(f"Target Mars IP : {MARS_IP}")
    print(f"Gate           : {MARS_IP}:{GATE_PORT}")
    print(f"Reality Sink   : {MARS_IP}:{SINK_PORT}")
    print()

    gate_ok = await tcp_check(
        "MARS GATE",
        MARS_IP,
        GATE_PORT,
    )

    sink_ok = await tcp_check(
        "MARS REALITY SINK",
        MARS_IP,
        SINK_PORT,
    )

    if not gate_ok:
        print()
        print("[ABORT] Mars gate is not reachable.")
        return

    if not sink_ok:
        print()
        print("[WARNING] Mars sink is not reachable.")

    run_id, operation_id, manifest, frame = build_frame()

    target_url = f"http://{MARS_IP}:{GATE_PORT}"

    print()
    print("[*] Sending ONE Earth -> Mars frame")
    print(f"Run ID       : {run_id}")
    print(f"Operation ID : {operation_id}")
    print(f"Target       : {target_url}")
    print()

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=3.0,
                read=10.0,
                write=10.0,
                pool=10.0,
            )
        ) as client:

            started = time.perf_counter()

            response = await client.post(
                target_url,
                content=frame,
                headers={
                    "Content-Type": "application/octet-stream"
                },
            )

            elapsed_ms = (
                time.perf_counter() - started
            ) * 1000

            print("[RESPONSE]")
            print(f"HTTP status : {response.status_code}")
            print(f"Latency     : {elapsed_ms:.2f} ms")
            print(f"Body        : {response.text[:1000]}")

    except Exception as exc:
        print()
        print("[TRANSPORT FAILURE]")
        print(f"{type(exc).__name__}: {exc}")
        return

    print()
    print("[MANIFEST SENT]")
    print(json.dumps(manifest, indent=2, sort_keys=True))

    print()
    print(f"[SEARCH ON MARS FOR RUN ID]")
    print(run_id)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )

    asyncio.run(main())
