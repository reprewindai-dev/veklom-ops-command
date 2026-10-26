import argparse
import asyncio
import hashlib
import json
import math
import os
import struct
import sys
import time
from collections import Counter
from pathlib import Path

try:
    import httpx
except ImportError:
    print("[SYSTEM] Missing 'httpx'. Install it with: python -m pip install httpx")
    sys.exit(1)

DEFAULT_TARGET_IP = "192.168.28.11"
DEFAULT_TARGET_PORT = 8550
DEFAULT_LINEAGE_ID = "STABLE_DATA_PLANE_V1"
DEFAULT_CURRENT_EPOCH = 4
RAMP_LEVELS = [(50, 2500), (100, 2500), (200, 2500), (400, 2500)]
REPLAY_UNIQUE_OPERATIONS = 200
REVERSE_ORDER_OPERATIONS = 500
REVERSE_RACE_OPERATIONS = 500
STALE_EPOCH_OPERATIONS = 500
START_STEP = 245
INCLUDE_CORRELATION_METADATA = True


def parse_args():
    p = argparse.ArgumentParser(description="Veklom Earth -> Mars falsifier")
    p.add_argument("--target-ip", default=DEFAULT_TARGET_IP)
    p.add_argument("--target-port", type=int, default=DEFAULT_TARGET_PORT)
    p.add_argument("--lineage-id", default=DEFAULT_LINEAGE_ID)
    p.add_argument("--epoch", type=int, default=DEFAULT_CURRENT_EPOCH)
    p.add_argument("--evidence-root", default=".")
    p.add_argument("--fsync-every", type=int, default=1)
    p.add_argument("--skip-reverse-race", action="store_true")
    return p.parse_args()


class ProductionPayloadTransformer:
    def __init__(self, target_url, lineage_id, epoch, run_id):
        self.target_url = target_url
        self.lineage_id = lineage_id
        self.epoch = epoch
        self.run_id = run_id

    def generate_compliant_frame(self, step_index, epoch=None):
        selected_epoch = self.epoch if epoch is None else epoch
        timestamp = time.time_ns()
        operation_id = hashlib.sha256(
            f"{self.run_id}:{self.lineage_id}:{selected_epoch}:{step_index}".encode()
        ).hexdigest()
        raw_manifest = f"{self.lineage_id}:{selected_epoch}:{step_index}:{timestamp}"
        token_hash = hashlib.sha256(raw_manifest.encode("utf-8")).hexdigest()
        manifest = {
            "lineage_id": self.lineage_id,
            "epoch": selected_epoch,
            "step": step_index,
            "timestamp_ns": timestamp,
            "signature_hex": token_hash,
            "payload": f"SYNCHRONIZE_REALITY_STATE_STEP_{step_index}",
        }
        if INCLUDE_CORRELATION_METADATA:
            manifest["run_id"] = self.run_id
            manifest["operation_id"] = operation_id
        serialized = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")
        frame = struct.pack("!BI", 0x51, len(serialized)) + serialized
        return frame, operation_id


class DurableEvidenceWriter:
    def __init__(self, path, fsync_every=1):
        if fsync_every < 1:
            raise ValueError("fsync_every must be >= 1")
        self.path = Path(path)
        self.fsync_every = fsync_every
        self.lock = asyncio.Lock()
        self.records_since_sync = 0

    async def append(self, record):
        line = json.dumps(record, sort_keys=True) + "\n"
        async with self.lock:
            await asyncio.to_thread(self._append_blocking, line)

    def _append_blocking(self, line):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            self.records_since_sync += 1
            if self.records_since_sync >= self.fsync_every:
                os.fsync(f.fileno())
                self.records_since_sync = 0

    async def force_sync(self):
        async with self.lock:
            await asyncio.to_thread(self._force_sync_blocking)

    def _force_sync_blocking(self):
        with self.path.open("a", encoding="utf-8") as f:
            f.flush()
            os.fsync(f.fileno())
        self.records_since_sync = 0


async def preflight_tcp(target_ip, target_port):
    print(f"[*] TCP preflight -> {target_ip}:{target_port}")
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(target_ip, target_port), timeout=3.0)
        writer.close()
        await writer.wait_closed()
        print("[OK] Mars TCP ingress is reachable.")
        return True
    except Exception as exc:
        print(f"[FAIL] Mars TCP ingress unavailable: {type(exc).__name__}: {exc}")
        return False


async def dispatch(client, semaphore, target_url, phase, frame, operation_id, step, attempt, evidence_writer):
    async with semaphore:
        started_ns = time.time_ns()
        record = {
            "phase": phase,
            "operation_id": operation_id,
            "step": step,
            "attempt": attempt,
            "started_ns": started_ns,
        }
        try:
            response = await client.post(
                target_url,
                content=frame,
                headers={"Content-Type": "application/octet-stream"},
            )
            finished_ns = time.time_ns()
            record.update({
                "transport_result": "HTTP_RESPONSE",
                "status_code": response.status_code,
                "latency_ms": (finished_ns - started_ns) / 1_000_000,
                "response_preview": response.text[:250],
                "finished_ns": finished_ns,
            })
        except Exception as exc:
            finished_ns = time.time_ns()
            record.update({
                "transport_result": "TRANSPORT_FAILURE",
                "error_type": type(exc).__name__,
                "error": str(exc)[:250],
                "latency_ms": (finished_ns - started_ns) / 1_000_000,
                "finished_ns": finished_ns,
            })
        await evidence_writer.append(record)
        return record


async def run_batch(client, target_url, phase, requests, concurrency, evidence_writer):
    semaphore = asyncio.Semaphore(concurrency)
    print(f"\n[*] PHASE {phase}: {len(requests)} requests @ concurrency={concurrency}")
    started = time.perf_counter()
    tasks = [
        dispatch(
            client, semaphore, target_url, phase,
            item["frame"], item["operation_id"], item["step"], item["attempt"],
            evidence_writer,
        )
        for item in requests
    ]
    results = await asyncio.gather(*tasks)
    await evidence_writer.force_sync()
    elapsed = time.perf_counter() - started
    rate = len(requests) / elapsed if elapsed > 0 else 0.0
    print(f"[+] {phase} finished in {elapsed:.3f}s ({rate:.1f} req/s)")
    return results, elapsed


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - index) + ordered[hi] * (index - lo)


def phase_summary(records):
    http_status = Counter(r["status_code"] for r in records if "status_code" in r)
    failures = Counter(r.get("error_type") for r in records if r["transport_result"] == "TRANSPORT_FAILURE")
    latencies = [r["latency_ms"] for r in records if "latency_ms" in r]
    return {
        "requests": len(records),
        "http_responses": sum(http_status.values()),
        "http_status_distribution": dict(http_status),
        "transport_failures": dict(failures),
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "max": max(latencies) if latencies else None,
        },
    }


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def make_batch(transformer, start_step, count, attempt, epoch=None):
    batch = []
    for step in range(start_step, start_step + count):
        frame, operation_id = transformer.generate_compliant_frame(step, epoch=epoch)
        batch.append({"frame": frame, "operation_id": operation_id, "step": step, "attempt": attempt})
    return batch


async def main():
    args = parse_args()
    run_id = f"EARTH_MARS_FALSIFIER_{time.time_ns()}"
    target_url = f"http://{args.target_ip}:{args.target_port}"

    evidence_root = Path(args.evidence_root).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_dir = evidence_root / f"evidence_{run_id}"
    evidence_dir.mkdir(parents=True, exist_ok=False)

    jsonl_path = evidence_dir / "client_requests.jsonl"
    summary_path = evidence_dir / "summary.json"
    manifest_path = evidence_dir / "SHA256SUMS.txt"
    jsonl_path.touch()

    evidence_writer = DurableEvidenceWriter(jsonl_path, fsync_every=args.fsync_every)

    print("\n" + "=" * 78)
    print(" VEKLOM EARTH -> MARS TRANSPORT / REPLAY / ORDERING FALSIFIER")
    print("=" * 78)
    print(f" Run ID       : {run_id}")
    print(f" Target       : {target_url}")
    print(f" Lineage      : {args.lineage_id}")
    print(f" Current epoch: {args.epoch}")
    print(f" Evidence     : {evidence_dir}")
    print(f" fsync every  : {args.fsync_every}")

    if not await preflight_tcp(args.target_ip, args.target_port):
        summary_path.write_text(json.dumps({
            "run_id": run_id,
            "status": "ABORTED_PREFLIGHT",
            "target_ip": args.target_ip,
            "target_port": args.target_port,
            "reason": "TCP ingress unreachable",
        }, indent=2, sort_keys=True), encoding="utf-8")
        print("\n[ABORT] Correct endpoint is not reachable. No falsification battery was executed.")
        return

    transformer = ProductionPayloadTransformer(target_url, args.lineage_id, args.epoch, run_id)
    summaries = {}
    next_step = START_STEP

    limits = httpx.Limits(max_keepalive_connections=400, max_connections=800)
    timeout = httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=10.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout, http2=False) as client:
        for concurrency, count in RAMP_LEVELS:
            phase = f"RAMP_C{concurrency}"
            batch = make_batch(transformer, next_step, count, "ORIGINAL")
            next_step += count
            records, elapsed = await run_batch(client, target_url, phase, batch, concurrency, evidence_writer)
            summaries[phase] = {**phase_summary(records), "elapsed_seconds": elapsed, "request_rate": len(records) / elapsed if elapsed else 0.0}

        replay_batch = []
        for step in range(next_step, next_step + REPLAY_UNIQUE_OPERATIONS):
            frame, operation_id = transformer.generate_compliant_frame(step)
            replay_batch.append({"frame": frame, "operation_id": operation_id, "step": step, "attempt": "REPLAY_A"})
            replay_batch.append({"frame": frame, "operation_id": operation_id, "step": step, "attempt": "REPLAY_B"})
        next_step += REPLAY_UNIQUE_OPERATIONS
        records, elapsed = await run_batch(client, target_url, "EXACT_REPLAY", replay_batch, 200, evidence_writer)
        summaries["EXACT_REPLAY"] = {**phase_summary(records), "elapsed_seconds": elapsed, "unique_operation_ids": REPLAY_UNIQUE_OPERATIONS, "http_attempts": len(replay_batch)}

        reverse_strict = make_batch(transformer, next_step, REVERSE_ORDER_OPERATIONS, "REVERSED_STRICT")
        next_step += REVERSE_ORDER_OPERATIONS
        reverse_strict.reverse()
        records, elapsed = await run_batch(client, target_url, "REVERSE_ORDER_STRICT", reverse_strict, 1, evidence_writer)
        summaries["REVERSE_ORDER_STRICT"] = {**phase_summary(records), "elapsed_seconds": elapsed, "sender_submission_order": "descending step order", "concurrency": 1}

        if not args.skip_reverse_race:
            reverse_race = make_batch(transformer, next_step, REVERSE_RACE_OPERATIONS, "REVERSED_RACE")
            next_step += REVERSE_RACE_OPERATIONS
            reverse_race.reverse()
            records, elapsed = await run_batch(client, target_url, "REVERSE_ORDER_RACE", reverse_race, 200, evidence_writer)
            summaries["REVERSE_ORDER_RACE"] = {**phase_summary(records), "elapsed_seconds": elapsed, "sender_batch_direction": "descending steps before async race", "concurrency": 200}

        stale_epoch = args.epoch - 1
        stale_batch = make_batch(transformer, next_step, STALE_EPOCH_OPERATIONS, f"STALE_EPOCH_{stale_epoch}", epoch=stale_epoch)
        next_step += STALE_EPOCH_OPERATIONS
        records, elapsed = await run_batch(client, target_url, "STALE_EPOCH", stale_batch, 100, evidence_writer)
        summaries["STALE_EPOCH"] = {**phase_summary(records), "elapsed_seconds": elapsed, "submitted_epoch": stale_epoch, "expected_current_epoch": args.epoch}

    await evidence_writer.force_sync()

    summary = {
        "run_id": run_id,
        "source_role": "EARTH",
        "target_role": "MARS",
        "target_ip": args.target_ip,
        "target_port": args.target_port,
        "lineage_id": args.lineage_id,
        "current_epoch": args.epoch,
        "fsync_every": args.fsync_every,
        "phases": summaries,
        "important_notes": [
            "HTTP 200 proves only that an HTTP response was returned; Mars-side ledger/state readback is required to establish consequence truth.",
            "signature_hex is populated with a SHA-256 digest in this harness; it is not an Ed25519 signature.",
            "REVERSE_ORDER_STRICT uses concurrency=1; REVERSE_ORDER_RACE intentionally does not guarantee receiver arrival order.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest_lines = []
    for artifact in [jsonl_path, summary_path, Path(__file__).resolve()]:
        if artifact.exists():
            manifest_lines.append(f"{sha256_file(artifact)}  {artifact.name}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print("\n" + "=" * 78)
    print(" CLIENT-SIDE BATTERY COMPLETE")
    print("=" * 78)
    print(f"Run ID: {run_id}\n")
    for phase, result in summaries.items():
        print(f"{phase}:")
        print(json.dumps(result, indent=2))
        print()
    print("[EVIDENCE]")
    print(f"Directory: {evidence_dir}")
    print(f"Requests : {jsonl_path}")
    print(f"Summary  : {summary_path}")
    print(f"Hashes   : {manifest_path}")
    print(f"\n[NEXT] On Mars, preserve receiver ledger/state and search for Run ID: {run_id}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
