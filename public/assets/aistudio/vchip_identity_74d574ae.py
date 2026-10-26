import os, json, hashlib, time, hmac
from dataclasses import dataclass, asdict
from typing import Optional, Tuple

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False

class FallbackSigningKey:
    def __init__(self, seed: Optional[bytes] = None):
        self._seed = seed or os.urandom(32)
        self.verify_key = FallbackVerifyKey(self._seed)
    def sign(self, message: bytes) -> bytes:
        sig = hmac.new(self._seed, message, hashlib.sha256).digest()
        return sig + message
    def encode(self) -> bytes:
        return self._seed
    @classmethod
    def from_seed(cls, seed: bytes):
        return cls(seed)

class FallbackVerifyKey:
    def __init__(self, seed: bytes):
        self._seed = seed
    def verify(self, signed_message: bytes) -> bytes:
        sig = signed_message[:32]
        message = signed_message[32:]
        expected = hmac.new(self._seed, message, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("Bad signature")
        return message
    def encode(self) -> bytes:
        return self._seed

if not NACL_AVAILABLE:
    SigningKey = FallbackSigningKey
    VerifyKey = FallbackVerifyKey
    BadSignatureError = ValueError

@dataclass
class VChipIdentity:
    execution_id: str
    epoch: int
    holder_id: str
    authority_public_key: str
    state_root: str
    evidence_head: str
    def to_dict(self) -> dict: return asdict(self)
    def to_json(self) -> str: return json.dumps(self.to_dict(), sort_keys=True)
    @classmethod
    def from_dict(cls, d: dict): return cls(**d)

@dataclass
class AuthorityRecord:
    execution_id: str
    current_epoch: int
    current_holder: str
    authority_public_key: str
    previous_evidence_head: str
    def to_dict(self) -> dict: return asdict(self)
    def to_json(self) -> str: return json.dumps(self.to_dict(), sort_keys=True)
    @classmethod
    def from_dict(cls, d: dict): return cls(**d)

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
        d = {"execution_id": self.execution_id, "from_epoch": self.from_epoch, "to_epoch": self.to_epoch, "from_holder": self.from_holder, "to_holder": self.to_holder, "state_root": self.state_root, "evidence_head": self.evidence_head, "next_public_key": self.next_public_key}
        return json.dumps(d, sort_keys=True).encode("utf-8")
    def to_dict(self) -> dict: return asdict(self)
    @classmethod
    def from_dict(cls, d: dict): return cls(**d)

@dataclass
class ConsequenceRequest:
    execution_id: str
    epoch: int
    holder_id: str
    operation_id: str
    signing_key_public: str
    payload: str
    signature: str = ""
    def canonical_bytes(self) -> bytes:
        d = {"execution_id": self.execution_id, "epoch": self.epoch, "holder_id": self.holder_id, "operation_id": self.operation_id, "signing_key_public": self.signing_key_public, "payload": self.payload}
        return json.dumps(d, sort_keys=True).encode("utf-8")

ALLOW = "ALLOW"
DENY = "DENY"
DENY_STALE_EPOCH = "DENY_STALE_EPOCH"
DENY_WRONG_HOLDER = "DENY_WRONG_HOLDER"
DENY_WRONG_KEY = "DENY_WRONG_KEY"
DENY_BAD_SIGNATURE = "DENY_BAD_SIGNATURE"
DENY_WRONG_EXECUTION = "DENY_WRONG_EXECUTION"
DENY_AUTHORITY_UNREACHABLE = "DENY_AUTHORITY_UNREACHABLE"

def validate_consequence(request: ConsequenceRequest, authority_record: AuthorityRecord) -> str:
    if request.execution_id != authority_record.execution_id: return DENY_WRONG_EXECUTION
    if request.epoch != authority_record.current_epoch: return DENY_STALE_EPOCH
    if request.holder_id != authority_record.current_holder: return DENY_WRONG_HOLDER
    if request.signing_key_public != authority_record.authority_public_key: return DENY_WRONG_KEY
    try:
        key_bytes = bytes.fromhex(request.signing_key_public)
        vk = VerifyKey(key_bytes)
        sig_bytes = bytes.fromhex(request.signature)
        canonical = request.canonical_bytes()
        vk.verify(sig_bytes + canonical)
    except Exception:
        return DENY_BAD_SIGNATURE
    return ALLOW

def compute_evidence_head(previous_head, execution_id, epoch, holder_id, operation_id, previous_state_root, new_state_root, consequence, manifestation_receipt) -> str:
    canonical = json.dumps({"previous_head": previous_head, "execution_id": execution_id, "epoch": epoch, "holder_id": holder_id, "operation_id": operation_id, "previous_state_root": previous_state_root, "new_state_root": new_state_root, "consequence": consequence, "manifestation_receipt": manifestation_receipt}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

def compute_state_root(state: dict) -> str:
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()

def generate_keypair() -> Tuple[object, str, str]:
    sk = SigningKey(os.urandom(32))
    return sk, sk.encode().hex(), sk.verify_key.encode().hex()

def sign_bytes(signing_key, message: bytes) -> str:
    signed = signing_key.sign(message)
    return signed.signature.hex() if NACL_AVAILABLE else signed[:32].hex()

def create_handoff(identity: VChipIdentity, signing_key, to_holder: str, next_public_key_hex: str) -> HandoffPackage:
    pkg = HandoffPackage(execution_id=identity.execution_id, from_epoch=identity.epoch, to_epoch=identity.epoch + 1, from_holder=identity.holder_id, to_holder=to_holder, state_root=identity.state_root, evidence_head=identity.evidence_head, next_public_key=next_public_key_hex)
    pkg.signature = sign_bytes(signing_key, pkg.canonical_bytes())
    return pkg

def verify_and_accept_handoff(pkg: HandoffPackage, authority_record: AuthorityRecord) -> str:
    if pkg.execution_id != authority_record.execution_id: return DENY_WRONG_EXECUTION
    if pkg.from_epoch != authority_record.current_epoch: return DENY_STALE_EPOCH
    if pkg.from_holder != authority_record.current_holder: return DENY_WRONG_HOLDER
    if pkg.to_epoch != pkg.from_epoch + 1: return DENY_STALE_EPOCH
    try:
        key_bytes = bytes.fromhex(authority_record.authority_public_key)
        vk = VerifyKey(key_bytes)
        sig_bytes = bytes.fromhex(pkg.signature)
        vk.verify(sig_bytes + pkg.canonical_bytes())
    except Exception:
        return DENY_BAD_SIGNATURE
    return ALLOW
