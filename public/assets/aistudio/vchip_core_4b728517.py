import os
import sys
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Optional, Tuple

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    raise RuntimeError("PyNaCl is mandatory for the physical V-Chip proof. Run: pip install pynacl")

@dataclass
class VChipIdentity:
    execution_id: str
    epoch: int
    holder_id: str
    authority_public_key: str
    state_root: str
    evidence_head: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'VChipIdentity':
        return cls(**d)

@dataclass
class AuthorityRecord:
    execution_id: str
    current_epoch: int
    current_holder: str
    authority_public_key: str
    previous_evidence_head: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'AuthorityRecord':
        return cls(**d)

@dataclass
class HandoffPackage:
    execution_id: str
    from_epoch: int
    to_epoch: int
    from_holder: str
    to_holder: str
    state_root: str
    evidence_head: str
    next_public_key: str
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {
            "execution_id": self.execution_id,
            "from_epoch": self.from_epoch,
            "to_epoch": self.to_epoch,
            "from_holder": self.from_holder,
            "to_holder": self.to_holder,
            "state_root": self.state_root,
            "evidence_head": self.evidence_head,
            "next_public_key": self.next_public_key,
        }
        return json.dumps(d, sort_keys=True).encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'HandoffPackage':
        return cls(**d)

@dataclass
class ConsequenceRequest:
    execution_id: str
    epoch: int
    holder_id: str
    operation_id: str
    signing_key_public: str
    state_root: str
    evidence_head: str
    payload_digest: str
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {
            "execution_id": self.execution_id,
            "epoch": self.epoch,
            "holder_id": self.holder_id,
            "operation_id": self.operation_id,
            "signing_key_public": self.signing_key_public,
            "state_root": self.state_root,
            "evidence_head": self.evidence_head,
            "payload_digest": self.payload_digest,
        }
        return json.dumps(d, sort_keys=True).encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'ConsequenceRequest':
        return cls(**d)

@dataclass
class ConsequencePermit:
    execution_id: str
    epoch: int
    holder_id: str
    operation_id: str
    state_root: str
    evidence_head: str
    authority_signature: str = ""

    def canonical_bytes(self) -> bytes:

        d = {
            "execution_id": self.execution_id,
            "epoch": self.epoch,
            "holder_id": self.holder_id,
            "operation_id": self.operation_id,
            "state_root": self.state_root,
            "evidence_head": self.evidence_head,
        }
        return json.dumps(d, sort_keys=True).encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'ConsequencePermit':
        return cls(**d)

ALLOW = "ALLOW"
DENY = "DENY"
DENY_STALE_EPOCH = "DENY_STALE_EPOCH"
DENY_WRONG_HOLDER = "DENY_WRONG_HOLDER"
DENY_WRONG_KEY = "DENY_WRONG_KEY"
DENY_BAD_SIGNATURE = "DENY_BAD_SIGNATURE"
DENY_WRONG_EXECUTION = "DENY_WRONG_EXECUTION"
DENY_REPLAYED_OPERATION = "DENY_REPLAYED_OPERATION"
DENY_STATE_MISMATCH = "DENY_STATE_MISMATCH"
DENY_AUTHORITY_UNREACHABLE = "DENY_AUTHORITY_UNREACHABLE"
DENY_NO_PERMIT = "DENY_NO_PERMIT"

def compute_evidence_head(previous_head, execution_id, epoch, holder_id, operation_id, previous_state_root, new_state_root, consequence, manifestation_receipt) -> str:
    canonical = json.dumps({
        "previous_head": previous_head,
        "execution_id": execution_id,
        "epoch": epoch,
        "holder_id": holder_id,
        "operation_id": operation_id,
        "previous_state_root": previous_state_root,
        "new_state_root": new_state_root,
        "consequence": consequence,
        "manifestation_receipt": manifestation_receipt,
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

def compute_state_root(state: dict) -> str:
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()

def generate_keypair() -> Tuple[SigningKey, str, str]:
    sk = SigningKey(os.urandom(32))
    return sk, sk.encode().hex(), sk.verify_key.encode().hex()

def sign_bytes(signing_key: SigningKey, message: bytes) -> str:
    return signing_key.sign(message).signature.hex()

def verify_signature(public_key_hex: str, signature_hex: str, message_bytes: bytes) -> bool:
    try:
        vk = VerifyKey(bytes.fromhex(public_key_hex))
        vk.verify(bytes.fromhex(signature_hex) + message_bytes)
        return True
    except Exception:
        return False
