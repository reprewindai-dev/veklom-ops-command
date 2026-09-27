"""Smoke tests for failure gates; run with `python self_test.py`."""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_ops import issues

root = Path(__file__).parent
schema = json.loads((root / "veklom-ops.schema.json").read_text())
example = json.loads((root / "veklom-ops.example.json").read_text())


def rejects(changed, text):
    result = issues(changed, schema)
    assert any(text in error for error in result), result


assert not issues(example, schema)

bad = copy.deepcopy(example)
bad["work_items"][0]["reviewer"] = "codex"
rejects(bad, "owner cannot be reviewer")

bad = copy.deepcopy(example)
bad["work_items"][0]["status"] = "ACTIVE"
rejects(bad, "branch")

bad = copy.deepcopy(example)
next(item for item in bad["work_items"] if item["id"] == "ANCHOR-001")["priority"] = 1
rejects(bad, "priority override")

bad = copy.deepcopy(example)
bad["change_events"].append({
    "id": "CHG-1", "release_id": "unknown", "phase": "CHANGED",
    "actor": "antigravity", "reason": "unreviewed deploy",
    "runtime_id": "production-unknown-until-inventory", "component_ids": [],
    "before_refs": [], "after_refs": [], "rollback_ref": "unknown",
    "public_check_evidence_ids": [], "at": "2026-09-27T03:20:00Z",
})
rejects(bad, "'codex' was expected")

bad = copy.deepcopy(example)
bad["policy"]["production_api_key"] = "do-not-store-secrets"
rejects(bad, "Additional properties are not allowed")

bad = copy.deepcopy(example)
bad["release_candidates"].append({
    "id": "RC-TEST", "lane": "anchor", "status": "READY",
    "components": [{"id": "cappo", "repo": "cappo-backend", "deployment_platform": "docker", "commit_sha": "a" * 40,
                    "image_digest": "sha256:" + "b" * 64, "deployment_id": None}],
    "canary_runtime_id": "canary-unknown-until-inventory",
    "production_runtime_id": "production-unknown-until-inventory",
    "gates": {
        name: "PASS" for name in (
            "signup_activation_login", "workspace", "authority_allow", "unauthorized_deny",
            "physical_effect", "independent_readback", "pgl_verified", "revoke_deny",
            "replay_deny", "lost_ack_reconciled", "sdk", "mcp", "anchor_session"
        )
    },
    "canary_evidence_ids": [], "production_evidence_ids": [],
    "approved_by": "Anthony", "rollback_ref": "previous-digest",
    "updated_at": "2026-09-27T03:20:00Z",
})
rejects(bad, "ready release needs canary evidence")

bad = copy.deepcopy(example)
bad["baseline"]["runtimes"][0]["services"].append({
    "id": "veklom-byos-backend", "repo": "veklom-byos-backend",
    "deployment_platform": "docker", "commit_sha": None, "image_digest": None,
    "container_id": None, "migration": None, "health": "UNKNOWN",
    "observed_at": None,
})
rejects(bad, "excluded infrastructure or service is forbidden")

bad = copy.deepcopy(example)
bad["baseline"]["runtimes"][0]["pages"]["deployment_platform"] = "vercel"
rejects(bad, "'cloudflare_pages' was expected")


def ready_anchor_fixture():
    manifest = copy.deepcopy(example)
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    commit_sha = "a" * 40
    image_digest = "sha256:" + "b" * 64
    canary = next(item for item in manifest["baseline"]["runtimes"] if item["environment"] == "canary")
    canary.update(hardware_node="test-owned-host", observed_at=observed_at)
    canary["pages"].update(project="test-pages", deployment_id="test-deployment", commit_sha=commit_sha,
                            health="PASS", observed_at=observed_at)
    canary["tunnels"][0].update(hostname="test.example", connector_id="test-tunnel",
                                origin_service="cappo", health="PASS", observed_at=observed_at)
    canary["services"].append({
        "id": "cappo", "repo": "cappo-backend", "deployment_platform": "docker",
        "commit_sha": commit_sha, "image_digest": image_digest, "container_id": "test-container",
        "migration": "test-migration", "health": "PASS", "observed_at": observed_at,
    })
    evidence_kinds = ("browser_trace", "authority_denial", "target_readback", "pgl_receipt",
                      "lost_ack", "anchor_run", "sdk", "mcp")
    evidence_ids = []
    for index, kind in enumerate(evidence_kinds):
        evidence_id = f"anchor-evidence-{index}"
        evidence_ids.append(evidence_id)
        is_external = kind in {"anchor_run", "lost_ack", "target_readback"}
        manifest["evidence"].append({
            "id": evidence_id,
            "environment": "anchor_external" if is_external else "canary",
            "kind": kind,
            "result": "PASS",
            "observed_at": observed_at,
            "operator": "codex",
            "subject": kind,
            "artifact_uri": f"evidence/{evidence_id}.json",
            "artifact_sha256": "c" * 64,
            "runtime_id": None if is_external else canary["runtime_id"],
            "component_id": "cappo",
            "commit_sha": commit_sha,
            "image_digest": image_digest,
            "operation_id": "anchor-operation-1" if is_external else None,
            "target_commit_count": 1 if kind == "target_readback" else None,
            "notes": "Synthetic fixture for validator self-test only; not production evidence.",
        })
    manifest["release_candidates"].append({
        "id": "ANCHOR-READY-TEST", "lane": "anchor", "status": "READY",
        "components": [{"id": "cappo", "repo": "cappo-backend", "deployment_platform": "docker",
                        "commit_sha": commit_sha, "image_digest": image_digest, "deployment_id": None}],
        "canary_runtime_id": canary["runtime_id"],
        "production_runtime_id": next(item["runtime_id"] for item in manifest["baseline"]["runtimes"]
                                       if item["environment"] == "production"),
        "gates": {name: "PASS" for name in (
            "signup_activation_login", "workspace", "authority_allow", "unauthorized_deny",
            "physical_effect", "independent_readback", "pgl_verified", "revoke_deny",
            "replay_deny", "lost_ack_reconciled", "sdk", "mcp", "anchor_session",
        )},
        "canary_evidence_ids": evidence_ids, "production_evidence_ids": [],
        "approved_by": "test-reviewer", "rollback_ref": "previous-test-digest",
        "updated_at": observed_at,
    })
    return manifest


good_anchor = ready_anchor_fixture()
assert not issues(good_anchor, schema), issues(good_anchor, schema)

bad = copy.deepcopy(good_anchor)
for item in bad["evidence"]:
    if item["kind"] in {"anchor_run", "lost_ack", "target_readback"}:
        item["environment"] = "canary"
        item["runtime_id"] = "canary-unknown-until-inventory"
rejects(bad, "Anchor release requires anchor_external")

bad = copy.deepcopy(good_anchor)
next(item for item in bad["evidence"] if item["kind"] == "target_readback")["operation_id"] = "different-operation"
rejects(bad, "must share an operation_id")

print("12/12 structural, negative, and Anchor evidence-binding cases passed")
