import os, sys, json, socket, hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vchip_identity import (VChipIdentity, AuthorityRecord, HandoffPackage, ConsequenceRequest, compute_evidence_head, compute_state_root, generate_keypair, sign_bytes, create_handoff, verify_and_accept_handoff, validate_consequence, ALLOW, SigningKey)

def manifestation_receipt() -> dict:
    return {"hostname": socket.gethostname(), "pid": os.getpid(), "parent_pid": os.getppid(), "timestamp": datetime.now(timezone.utc).isoformat(), "boot_id": hashlib.md5(f"{socket.gethostname()}-{os.getpid()}".encode()).hexdigest()[:12]}

class GovernedStateMachine:
    def __init__(self):
        self.state = {"counter": 0}
        self.evidence_chain = []
    def get_state_root(self) -> str: return compute_state_root(self.state)
    def apply_consequence(self, operation_id: str, identity: VChipIdentity) -> dict:
        prev_sr = self.get_state_root()
        prev_cnt = self.state["counter"]
        self.state["counter"] = prev_cnt + 1
        new_sr = self.get_state_root()
        rcpt = manifestation_receipt()
        new_head = compute_evidence_head(identity.evidence_head, identity.execution_id, identity.epoch, identity.holder_id, operation_id, prev_sr, new_sr, f"counter:{prev_cnt}->{self.state['counter']}", rcpt)
        entry = {"operation_id": operation_id, "execution_id": identity.execution_id, "epoch": identity.epoch, "holder_id": identity.holder_id, "previous_counter": prev_cnt, "new_counter": self.state["counter"], "previous_state_root": prev_sr, "new_state_root": new_sr, "previous_evidence_head": identity.evidence_head, "new_evidence_head": new_head, "manifestation": rcpt}
        self.evidence_chain.append(entry)
        return entry, new_sr, new_head
    def save_state(self, filepath: str):
        with open(filepath, "w") as f: json.dump({"state": self.state, "evidence_chain": self.evidence_chain}, f, indent=2)
    def load_state(self, filepath: str):
        with open(filepath, "r") as f: data = json.load(f)
        self.state = data["state"]; self.evidence_chain = data.get("evidence_chain", [])

class GovernedNode:
    def __init__(self, holder_id: str):
        self.holder_id = holder_id; self.signing_key = None; self.private_key_hex = None; self.public_key_hex = None
        self.identity = None; self.authority_record = None; self.state_machine = GovernedStateMachine()
    def initialize_as_origin(self, execution_id: str) -> VChipIdentity:
        self.signing_key, self.private_key_hex, self.public_key_hex = generate_keypair()
        init_sr = self.state_machine.get_state_root()
        gen_head = hashlib.sha256(json.dumps({"genesis": True, "execution_id": execution_id, "epoch": 1, "holder_id": self.holder_id, "state_root": init_sr, "timestamp": datetime.now(timezone.utc).isoformat()}, sort_keys=True).encode()).hexdigest()
        self.identity = VChipIdentity(execution_id=execution_id, epoch=1, holder_id=self.holder_id, authority_public_key=self.public_key_hex, state_root=init_sr, evidence_head=gen_head)
        self.authority_record = AuthorityRecord(execution_id=execution_id, current_epoch=1, current_holder=self.holder_id, authority_public_key=self.public_key_hex, previous_evidence_head="GENESIS")
        return self.identity
    def execute_consequence(self, operation_id: str) -> tuple:
        req = ConsequenceRequest(execution_id=self.identity.execution_id, epoch=self.identity.epoch, holder_id=self.holder_id, operation_id=operation_id, signing_key_public=self.public_key_hex, payload=f"increment_counter_{operation_id}")
        req.signature = sign_bytes(self.signing_key, req.canonical_bytes())
        v = validate_consequence(req, self.authority_record)
        if v != ALLOW: return v, None
        ev, new_sr, new_hd = self.state_machine.apply_consequence(operation_id, self.identity)
        self.identity.state_root = new_sr; self.identity.evidence_head = new_hd; self.authority_record.previous_evidence_head = new_hd
        return ALLOW, ev
    def produce_handoff(self, to_holder: str, next_public_key_hex: str) -> HandoffPackage:
        return create_handoff(self.identity, self.signing_key, to_holder, next_public_key_hex)
    def receive_handoff(self, pkg: HandoffPackage, authority_record: AuthorityRecord, state_machine: GovernedStateMachine) -> str:
        v = verify_and_accept_handoff(pkg, authority_record)
        if v != ALLOW: return v
        self.identity = VChipIdentity(execution_id=pkg.execution_id, epoch=pkg.to_epoch, holder_id=self.holder_id, authority_public_key=self.public_key_hex, state_root=pkg.state_root, evidence_head=pkg.evidence_head)
        self.authority_record = AuthorityRecord(execution_id=pkg.execution_id, current_epoch=pkg.to_epoch, current_holder=self.holder_id, authority_public_key=self.public_key_hex, previous_evidence_head=pkg.evidence_head)
        self.state_machine = state_machine
        return ALLOW
    def save_full_state(self, directory: str):
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "identity.json"), "w") as f: json.dump(self.identity.to_dict(), f, indent=2)
        with open(os.path.join(directory, "authority_record.json"), "w") as f: json.dump(self.authority_record.to_dict(), f, indent=2)
        with open(os.path.join(directory, "private_key.hex"), "w") as f: f.write(self.private_key_hex)
        with open(os.path.join(directory, "public_key.hex"), "w") as f: f.write(self.public_key_hex)
        self.state_machine.save_state(os.path.join(directory, "state_machine.json"))
    def restore_full_state(self, directory: str):
        with open(os.path.join(directory, "identity.json"), "r") as f: self.identity = VChipIdentity.from_dict(json.load(f))
        with open(os.path.join(directory, "authority_record.json"), "r") as f: self.authority_record = AuthorityRecord.from_dict(json.load(f))
        with open(os.path.join(directory, "private_key.hex"), "r") as f: self.private_key_hex = f.read().strip()
        with open(os.path.join(directory, "public_key.hex"), "r") as f: self.public_key_hex = f.read().strip()
        kb = bytes.fromhex(self.private_key_hex)
        self.signing_key = SigningKey(kb)
        self.state_machine = GovernedStateMachine()
        self.state_machine.load_state(os.path.join(directory, "state_machine.json"))
