"""Generate the versioned JSON Schema from small reusable definitions."""

import json
from pathlib import Path


def obj(properties, required=None):
    return {"type": "object", "properties": properties, "required": required or list(properties), "additionalProperties": False}


def array(item, min_items=0):
    return {"type": "array", "items": item, "minItems": min_items}


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


nonempty = {"type": "string", "minLength": 1}
date = {"type": "string", "format": "date-time"}
nullable_date = {"anyOf": [date, {"type": "null"}]}
sha = {"type": "string", "pattern": "^[a-fA-F0-9]{40}$"}
digest = {"type": "string", "pattern": "^sha256:[a-fA-F0-9]{64}$"}
nullable_sha = {"anyOf": [sha, {"type": "null"}]}
nullable_digest = {"anyOf": [digest, {"type": "null"}]}
nullable_string = {"anyOf": [nonempty, {"type": "null"}]}
agent = {"type": "string", "enum": ["codex", "antigravity", "devin"]}
status = {"type": "string", "enum": ["UNKNOWN", "BLOCKED", "PASS", "FAIL"]}
ids = array(nonempty)

service = obj({
    "id": nonempty,
    "repo": nonempty,
    "deployment_platform": {"const": "docker"},
    "commit_sha": nullable_sha,
    "image_digest": nullable_digest,
    "container_id": nullable_string,
    "migration": nullable_string,
    "health": status,
    "observed_at": nullable_date,
})
pages = obj({
    "deployment_platform": {"const": "cloudflare_pages"},
    "project": nonempty,
    "deployment_id": nullable_string,
    "commit_sha": nullable_sha,
    "health": status,
    "observed_at": nullable_date,
})
tunnel = obj({
    "deployment_platform": {"const": "cloudflare_tunnel"},
    "hostname": nonempty,
    "connector_id": nullable_string,
    "origin_service": nullable_string,
    "health": status,
    "observed_at": nullable_date,
})
runtime = obj({
    "runtime_id": nonempty,
    "environment": {"enum": ["production", "canary"]},
    "hardware_node": nullable_string,
    "hardware_ownership": {"const": "self_owned"},
    "services": array(service),
    "pages": pages,
    "tunnels": array(tunnel),
    "observed_at": nullable_date,
})

work = obj({
    "id": nonempty,
    "lane": {"enum": ["prod_user_journey", "anchor", "customer_use_case", "infra_incident"]},
    "priority": {"type": "integer", "minimum": 0, "maximum": 3},
    "priority_override_reason": nullable_string,
    "return_to_work_id": nullable_string,
    "owner": agent,
    "reviewer": agent,
    "status": {"enum": ["UNCLAIMED", "ACTIVE", "REVIEW", "CANARY", "BLOCKED", "PROMOTED"]},
    "outcome": nonempty,
    "runtime_id": nonempty,
    "branch": nullable_string,
    "base_sha": nullable_sha,
    "paths": array(nonempty),
    "depends_on": ids,
    "evidence_ids": ids,
    "blocker": nullable_string,
    "handoff": {"anyOf": [ref("handoff"), {"type": "null"}]},
    "updated_at": date,
})
work["allOf"] = [
    {"if": {"properties": {"status": {"enum": ["ACTIVE", "REVIEW", "CANARY", "PROMOTED"]}}, "required": ["status"]},
     "then": {"properties": {"branch": nonempty, "base_sha": sha}, "required": ["branch", "base_sha"]}},
    {"if": {"properties": {"status": {"const": "BLOCKED"}}, "required": ["status"]},
     "then": {"properties": {"blocker": nonempty}}},
]

evidence = obj({
    "id": nonempty,
    "environment": {"enum": ["local", "canary", "production", "anchor_external"]},
    "kind": {"enum": ["unit_test", "integration_test", "browser_trace", "authority_denial", "target_readback", "pgl_receipt", "lost_ack", "anchor_run", "sdk", "mcp", "runtime_health", "deployment_observation"]},
    "result": {"enum": ["PASS", "FAIL", "INDETERMINATE"]},
    "observed_at": date,
    "operator": agent,
    "subject": nonempty,
    "artifact_uri": nonempty,
    "artifact_sha256": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"},
    "runtime_id": nullable_string,
    "component_id": nullable_string,
    "commit_sha": nullable_sha,
    "image_digest": nullable_digest,
    "operation_id": nullable_string,
    "target_commit_count": {"anyOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]},
    "notes": nonempty,
})

gate_names = ["signup_activation_login", "workspace", "authority_allow", "unauthorized_deny", "physical_effect", "independent_readback", "pgl_verified", "revoke_deny", "replay_deny", "lost_ack_reconciled", "sdk", "mcp", "anchor_session"]
gates = obj({name: status for name in gate_names})

component = obj({
    "id": nonempty,
    "repo": nonempty,
    "deployment_platform": {"enum": ["docker", "cloudflare_pages"]},
    "commit_sha": sha,
    "image_digest": {"anyOf": [digest, {"type": "null"}]},
    "deployment_id": nullable_string,
})
component["allOf"] = [
    {"if": {"properties": {"deployment_platform": {"const": "docker"}}, "required": ["deployment_platform"]},
     "then": {"properties": {"image_digest": digest, "deployment_id": {"type": "null"}}}},
    {"if": {"properties": {"deployment_platform": {"const": "cloudflare_pages"}}, "required": ["deployment_platform"]},
     "then": {"properties": {"image_digest": {"type": "null"}, "deployment_id": nonempty}}},
]
release = obj({
    "id": nonempty,
    "lane": {"enum": ["prod_user_journey", "anchor", "customer_use_case"]},
    "status": {"enum": ["CANDIDATE", "READY", "PROMOTED", "ROLLED_BACK"]},
    "components": array(component, 1),
    "canary_runtime_id": nonempty,
    "production_runtime_id": nonempty,
    "gates": gates,
    "canary_evidence_ids": ids,
    "production_evidence_ids": ids,
    "approved_by": nullable_string,
    "rollback_ref": nullable_string,
    "updated_at": date,
})

change = obj({
    "id": nonempty,
    "release_id": nonempty,
    "phase": {"enum": ["INTENT", "CHANGED", "OBSERVED", "ROLLED_BACK"]},
    "actor": {"const": "codex"},
    "reason": nonempty,
    "runtime_id": nonempty,
    "component_ids": ids,
    "before_refs": ids,
    "after_refs": ids,
    "rollback_ref": nonempty,
    "public_check_evidence_ids": ids,
    "at": date,
})
change["allOf"] = [
    {"if": {"properties": {"phase": {"enum": ["CHANGED", "OBSERVED"]}}, "required": ["phase"]},
     "then": {"properties": {"after_refs": {"type": "array", "items": nonempty, "minItems": 1}}}},
    {"if": {"properties": {"phase": {"const": "OBSERVED"}}, "required": ["phase"]},
     "then": {"properties": {"public_check_evidence_ids": {"type": "array", "items": nonempty, "minItems": 1}}}},
]

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:veklom:production-ops:1",
    "title": "Veklom shared production operating state",
    "description": "Machine-readable coordination and release gate. Run validate_ops.py for cross-record checks.",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "updated_at", "agents", "policy", "baseline", "work_items", "evidence", "release_candidates", "change_events"],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "updated_at": date,
        "agents": obj({
            "codex": obj({"role": {"const": "integrator_release_owner"}, "primary": array(nonempty, 1)}),
            "antigravity": obj({"role": {"const": "secondary_executor"}, "primary": array(nonempty, 1)}),
            "devin": obj({"role": {"const": "helper_validator"}, "primary": array(nonempty, 1)}),
        }),
        "policy": obj({
            "max_active_total": {"const": 2},
            "max_active_per_runtime": {"const": 1},
            "production_change_actor": {"const": "codex"},
            "branch_model": {"const": "task_scoped_from_recorded_base_sha"},
            "promotion_mode": {"const": "exact_tested_digest"},
            "production_secrets_in_manifest": {"const": False},
            "allowed_surfaces": {"const": ["cloudflare_pages", "cloudflare_tunnel", "docker", "self_owned_hardware"]},
            "excluded_systems": {"const": ["vercel", "hetzner", "coolify", "byos", "veklom-byos-backend"]},
        }),
        "baseline": obj({"runtimes": array(runtime, 2), "observed_at": nullable_date}),
        "work_items": array(work),
        "evidence": array(evidence),
        "release_candidates": array(release),
        "change_events": array(change),
    },
    "$defs": {"handoff": obj({
        "from": agent,
        "to": agent,
        "branch": nonempty,
        "failure": nonempty,
        "next_action": nonempty,
        "at": date,
    })},
}

path = Path(__file__).with_name("veklom-ops.schema.json")
path.write_bytes((json.dumps(schema, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
print(path)
