#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "continuum" / "VEKLOM_CONTINUUM_MANIFEST.json"

def fail(msg: str) -> None:
    raise SystemExit("CONTINUUM_CONTRACT_INVALID: " + msg)

data = json.loads(MANIFEST.read_text(encoding="utf-8"))

if data.get("schema_version") != "1.0":
    fail("schema_version must be 1.0")

anchor = data.get("canonical_anchor") or {}
if anchor.get("accepted") is not True:
    fail("canonical continuum anchor must remain accepted")

rc1 = ((data.get("release_candidates") or {}).get("RC1") or {})
if rc1.get("accepted") is not False:
    fail("RC1 must remain explicitly unaccepted until a separate acceptance event changes it")

authority = ((data.get("ownership") or {}).get("consequence_authority") or {})
if authority.get("canonical") != "CAPPO" or authority.get("sole") is not True:
    fail("CAPPO must remain the sole canonical consequence authority")

required_invariants = {
    "I-COMPUTE-AUTHORITY-SEPARATION",
    "I-ACCEPTED-EFFECT",
    "I-EVIDENCE-NOT-PERMISSION",
    "I-MONOTONIC-AUTHORITY",
    "I-RC1-NOT-ANCHOR",
    "I-NO-DUPLICATE-CANONICAL-COMPONENTS",
}
seen = {x.get("id") for x in data.get("hard_invariants", [])}
missing = required_invariants - seen
if missing:
    fail("missing hard invariants: " + ", ".join(sorted(missing)))

programs = data.get("proof_programs")
if not isinstance(programs, list) or not programs:
    fail("proof_programs must be a non-empty list")

ids = set()
for p in programs:
    pid = p.get("program_id")
    if not pid:
        fail("program without program_id")
    if pid in ids:
        fail("duplicate program_id: " + pid)
    ids.add(pid)
    for field in ("acceptance", "proof_classification", "claim_scope", "establishes", "evidence_refs", "boundaries"):
        if not p.get(field):
            fail(f"{pid}: missing {field}")
    if "UNIVERSAL" in str(p.get("proof_classification", "")).upper():
        fail(f"{pid}: universal proof classification is prohibited without a formal narrow model")

requirements = data.get("integration_requirements") or []
if not any("public consequence contracts" in x for x in requirements):
    fail("missing CAPPO public-contract integration requirement")
if not any("VirtualDB" in x for x in requirements):
    fail("missing canonical VirtualDB export requirement")

print(f"CONTINUUM_CONTRACT_VALID programs={len(programs)} invariants={len(seen)}")
