"""Validate Veklom's shared operations manifest and cross-record release rules.

Usage: python validate_ops.py [manifest.json] [schema.json]
Requires: pip install 'jsonschema>=4,<5'
Exit 0 = structurally consistent; this does not independently attest real-world evidence.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


CORE = (
    "signup_activation_login", "workspace", "authority_allow", "unauthorized_deny",
    "physical_effect", "independent_readback", "pgl_verified", "revoke_deny",
    "replay_deny", "lost_ack_reconciled",
)
CUSTOMER = ("authority_allow", "unauthorized_deny", "physical_effect",
            "independent_readback", "pgl_verified", "replay_deny", "lost_ack_reconciled")
ANCHOR = (
    "authority_allow", "unauthorized_deny", "physical_effect", "independent_readback",
    "pgl_verified", "revoke_deny", "replay_deny", "lost_ack_reconciled",
    "sdk", "mcp", "anchor_session",
)
ACTIVE = {"ACTIVE", "REVIEW", "CANARY"}
SECRET_KEY = re.compile(r"(^|_)(api_key|password|private_key|access_token|secret|bearer_token)($|_)", re.I)
SECRET_VALUE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bsk-proj-[A-Za-z0-9_-]{16,}", re.I)
EXCLUDED_INFRA = re.compile(r"vercel|hetzner|coolify|(?:^|[^a-z])byos(?:[^a-z]|$)", re.I)


def issues(manifest: dict, schema: dict) -> list[str]:
    errors = [f"schema {'.'.join(map(str, error.path)) or '$'}: {error.message}"
              for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest)]
    if errors:
        return sorted(errors)

    def unique(collection: list[dict], field: str, label: str) -> None:
        for value, count in Counter(item[field] for item in collection).items():
            if count > 1:
                errors.append(f"duplicate {label}: {value}")

    def no_secrets(value: object, at: str = "$") -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if SECRET_KEY.search(key):
                    errors.append(f"secret-like field forbidden: {at}.{key}")
                no_secrets(nested, f"{at}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                no_secrets(nested, f"{at}[{index}]")
        elif isinstance(value, str) and SECRET_VALUE.search(value):
            errors.append(f"credential-like value forbidden: {at}")

    no_secrets(manifest)
    def check_infrastructure(value: str | None, label: str) -> None:
        if value and EXCLUDED_INFRA.search(value):
            errors.append(f"{label}: excluded infrastructure or service is forbidden: {value}")
    runtimes = manifest["baseline"]["runtimes"]
    tasks = manifest["work_items"]
    evidence = manifest["evidence"]
    releases = manifest["release_candidates"]
    changes = manifest["change_events"]
    for collection, field, label in (
        (runtimes, "runtime_id", "runtime_id"), (tasks, "id", "work item ID"),
        (evidence, "id", "evidence ID"), (releases, "id", "release ID"),
        (changes, "id", "change event ID"),
    ):
        unique(collection, field, label)

    runtime_by_id = {x["runtime_id"]: x for x in runtimes}
    evidence_by_id = {x["id"]: x for x in evidence}
    task_by_id = {x["id"]: x for x in tasks}
    release_by_id = {x["id"]: x for x in releases}
    production = [r for r in runtimes if r["environment"] == "production"]
    canary = [r for r in runtimes if r["environment"] == "canary"]
    if not production or not canary:
        errors.append("baseline must include a production and a canary runtime")

    for runtime in runtimes:
        unique(runtime["services"], "id", f"service in {runtime['runtime_id']}")
        check_infrastructure(runtime["hardware_node"], f"{runtime['runtime_id']} hardware")
        check_infrastructure(runtime["pages"]["project"], f"{runtime['runtime_id']} Pages project")
        for service in runtime["services"]:
            check_infrastructure(service["id"], f"{runtime['runtime_id']} service ID")
            check_infrastructure(service["repo"], f"{runtime['runtime_id']} repo")
        for tunnel in runtime["tunnels"]:
            check_infrastructure(tunnel["origin_service"], f"{runtime['runtime_id']} tunnel origin")
    active = [task for task in tasks if task["status"] in ACTIVE]
    if len(active) > manifest["policy"]["max_active_total"]:
        errors.append("work in progress exceeds max_active_total")
    for rid, count in Counter(task["runtime_id"] for task in active).items():
        if count > manifest["policy"]["max_active_per_runtime"]:
            errors.append(f"concurrent edits exceed max_active_per_runtime: {rid}")
    for task in tasks:
        tid = task["id"]
        if task["owner"] == task["reviewer"]:
            errors.append(f"{tid}: owner cannot be reviewer")
        if task["lane"] == "infra_incident" and task["priority"] != 0:
            errors.append(f"{tid}: production incident must have priority 0")
        if task["lane"] != "infra_incident" and task["priority"] == 0:
            errors.append(f"{tid}: priority 0 reserved for production incidents")
        if task["lane"] in {"anchor", "customer_use_case"} and task["priority"] == 1:
            if not task["priority_override_reason"] or not task["return_to_work_id"]:
                errors.append(f"{tid}: customer priority override needs reason and return-to task")
            elif task["return_to_work_id"] not in task_by_id:
                errors.append(f"{tid}: return-to task does not exist")
        if task["runtime_id"] not in runtime_by_id:
            errors.append(f"{tid}: runtime does not exist")
        for dependency in task["depends_on"]:
            if dependency not in task_by_id or dependency == tid:
                errors.append(f"{tid}: invalid dependency {dependency}")
        for eid in task["evidence_ids"]:
            if eid not in evidence_by_id:
                errors.append(f"{tid}: missing evidence {eid}")
        if task["handoff"]:
            handoff = task["handoff"]
            if handoff["to"] != task["owner"] or handoff["from"] == handoff["to"]:
                errors.append(f"{tid}: handoff does not match the current owner")
            if handoff["branch"] != task["branch"]:
                errors.append(f"{tid}: handoff branch differs from task branch")
        if task["status"] in ACTIVE | {"PROMOTED"}:
            expected = f"work/{tid.lower()}/{task['owner']}"
            if task["branch"] != expected:
                errors.append(f"{tid}: task-scoped branch must be {expected}")
    for i, first in enumerate(active):
        for second in active[i + 1:]:
            if first["branch"] == second["branch"]:
                errors.append(f"shared writable branch: {first['id']} and {second['id']}")
            if set(first["paths"]) & set(second["paths"]):
                errors.append(f"overlapping claimed paths: {first['id']} and {second['id']}")

    for ev in evidence:
        if ev["runtime_id"] and ev["runtime_id"] not in runtime_by_id:
            errors.append(f"{ev['id']}: runtime does not exist")
        if ev["environment"] in {"canary", "production"}:
            rt = runtime_by_id.get(ev["runtime_id"])
            if not rt or rt["environment"] != ev["environment"]:
                errors.append(f"{ev['id']}: evidence environment/runtime mismatch")
        if ev["kind"] == "target_readback" and ev["result"] == "PASS":
            if ev["target_commit_count"] is None or not ev["operation_id"]:
                errors.append(f"{ev['id']}: target readback needs count and operation ID")

    for release in releases:
        rid = release["id"]
        canary_rt = runtime_by_id.get(release["canary_runtime_id"])
        prod_rt = runtime_by_id.get(release["production_runtime_id"])
        if not canary_rt or canary_rt["environment"] != "canary":
            errors.append(f"{rid}: invalid canary runtime")
        if not prod_rt or prod_rt["environment"] != "production":
            errors.append(f"{rid}: invalid production runtime")
        unique(release["components"], "id", f"component in {rid}")
        for component in release["components"]:
            check_infrastructure(component["id"], f"{rid} component ID")
            check_infrastructure(component["repo"], f"{rid} component repo")
        for field in ("canary_evidence_ids", "production_evidence_ids"):
            expected_environment = "canary" if field.startswith("canary") else "production"
            for eid in release[field]:
                ev = evidence_by_id.get(eid)
                if not ev:
                    errors.append(f"{rid}: missing evidence {eid}")
                elif ev["environment"] != expected_environment and not (
                    expected_environment == "canary" and ev["environment"] == "anchor_external"
                ):
                    errors.append(f"{rid}: {eid} has wrong evidence environment")
                elif ev["result"] != "PASS":
                    errors.append(f"{rid}: {eid} is not passing evidence")
                elif ev["component_id"] not in {c["id"] for c in release["components"]}:
                    errors.append(f"{rid}: {eid} does not name a candidate component")
                else:
                    component = next(c for c in release["components"] if c["id"] == ev["component_id"])
                    if ev["commit_sha"] != component["commit_sha"] or ev["image_digest"] != component["image_digest"]:
                        errors.append(f"{rid}: {eid} evidence SHA/digest differs from candidate")
        if release["status"] not in {"READY", "PROMOTED"}:
            continue
        required = ANCHOR if release["lane"] == "anchor" else (
            CUSTOMER if release["lane"] == "customer_use_case" else CORE
        )
        for gate in required:
            if release["gates"][gate] != "PASS":
                errors.append(f"{rid}: {gate} must PASS for {release['status']}")
        if not release["canary_evidence_ids"] or not release["approved_by"] or not release["rollback_ref"]:
            errors.append(f"{rid}: ready release needs canary evidence, product approval, rollback ref")
        if canary_rt:
            observed = canary_rt["observed_at"]
            if not canary_rt["hardware_node"] or not observed or canary_rt["pages"]["health"] != "PASS" or any(t["health"] != "PASS" for t in canary_rt["tunnels"]):
                errors.append(f"{rid}: canary baseline/Page/Tunnel not observed healthy")
            elif not (timedelta(0) <= datetime.now(timezone.utc) - datetime.fromisoformat(observed.replace("Z", "+00:00")) <= timedelta(hours=24)):
                errors.append(f"{rid}: canary observation must be from the last 24 hours")
            for component in release["components"]:
                deployed = next((s for s in canary_rt["services"] if s["id"] == component["id"]), None)
                if component["image_digest"]:
                    if not deployed or deployed["health"] != "PASS" or deployed["image_digest"] != component["image_digest"] or deployed["commit_sha"] != component["commit_sha"]:
                        errors.append(f"{rid}: {component['id']} canary digest/SHA differs from tested candidate")
                elif canary_rt["pages"]["deployment_id"] != component["deployment_id"] or canary_rt["pages"]["commit_sha"] != component["commit_sha"]:
                    errors.append(f"{rid}: Pages deploy differs from tested candidate")
        good_canary = [evidence_by_id[eid] for eid in release["canary_evidence_ids"] if eid in evidence_by_id and evidence_by_id[eid]["result"] == "PASS"]
        required_kinds = {"browser_trace", "authority_denial", "target_readback", "pgl_receipt", "lost_ack"}
        present = {e["kind"] for e in good_canary}
        if release["lane"] == "anchor":
            required_kinds.update({"anchor_run", "sdk", "mcp"})
        for kind in required_kinds - present:
            errors.append(f"{rid}: missing canary/external {kind} evidence")
        if not any(e["kind"] == "target_readback" and e["target_commit_count"] == 1 for e in good_canary):
            errors.append(f"{rid}: no independently observed exactly-one target record")
        if release["lane"] == "anchor":
            external_anchor_runs = [e for e in good_canary
                                    if e["kind"] == "anchor_run" and e["environment"] == "anchor_external"]
            external_lost_acks = [e for e in good_canary
                                  if e["kind"] == "lost_ack" and e["environment"] == "anchor_external"]
            external_readbacks = [e for e in good_canary
                                  if e["kind"] == "target_readback" and e["environment"] == "anchor_external"
                                  and e["target_commit_count"] == 1]
            if not external_anchor_runs or not external_lost_acks or not external_readbacks:
                errors.append(f"{rid}: Anchor release requires anchor_external session, lost-ack, and exactly-one target-readback evidence")
            else:
                operation_sets = [
                    {e["operation_id"] for e in records if e["operation_id"]}
                    for records in (external_anchor_runs, external_lost_acks, external_readbacks)
                ]
                if not all(operation_sets) or not set.intersection(*operation_sets):
                    errors.append(f"{rid}: Anchor external session, lost-ack, and target-readback must share an operation_id")
        if release["status"] == "PROMOTED":
            if not release["production_evidence_ids"]:
                errors.append(f"{rid}: production evidence missing")
            if prod_rt:
                if not prod_rt["hardware_node"] or not prod_rt["observed_at"] or prod_rt["pages"]["health"] != "PASS" or any(t["health"] != "PASS" for t in prod_rt["tunnels"]):
                    errors.append(f"{rid}: production baseline/Page/Tunnel not observed healthy")
                for component in release["components"]:
                    deployed = next((s for s in prod_rt["services"] if s["id"] == component["id"]), None)
                    if component["image_digest"]:
                        if not deployed or deployed["health"] != "PASS" or deployed["image_digest"] != component["image_digest"] or deployed["commit_sha"] != component["commit_sha"]:
                            errors.append(f"{rid}: {component['id']} production != tested digest/SHA")
                    elif prod_rt["pages"]["deployment_id"] != component["deployment_id"] or prod_rt["pages"]["commit_sha"] != component["commit_sha"]:
                        errors.append(f"{rid}: production Pages != tested deploy")
            if not any(c["release_id"] == rid and c["phase"] == "OBSERVED" for c in changes):
                errors.append(f"{rid}: no OBSERVED production change")

    phase_rank = {"INTENT": 0, "CHANGED": 1, "OBSERVED": 2, "ROLLED_BACK": 2}
    history: dict[str, int] = {}
    for event in changes:
        eid, rid, phase = event["id"], event["release_id"], event["phase"]
        if rid not in release_by_id:
            errors.append(f"{eid}: unknown release ID")
        if event["runtime_id"] not in runtime_by_id or runtime_by_id[event["runtime_id"]]["environment"] != "production":
            errors.append(f"{eid}: not a production runtime")
        prior = history.get(rid, -1)
        if phase_rank[phase] != prior + 1:
            errors.append(f"{eid}: production phases must progress INTENT -> CHANGED -> OBSERVED/ROLLED_BACK")
        history[rid] = phase_rank[phase]
        if phase in {"CHANGED", "OBSERVED"} and (not event["before_refs"] or event["before_refs"] == event["after_refs"]):
            errors.append(f"{eid}: change needs distinct recorded before and after artifacts")
        for evidence_id in event["public_check_evidence_ids"]:
            if evidence_id not in evidence_by_id:
                errors.append(f"{eid}: missing public check evidence {evidence_id}")
    return sorted(errors)


def main() -> int:
    folder = Path(__file__).parent
    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else folder / "veklom-ops.example.json"
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else folder / "veklom-ops.schema.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = issues(manifest, schema)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"INVALID ({len(errors)} issues)")
        return 1
    print("VALID STRUCTURE AND CROSS-REFERENCES; live evidence still requires independent verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
