import json, os
from dataclasses import dataclass, asdict
try:
    from nacl.signing import SigningKey, VerifyKey
except ImportError:
    raise RuntimeError("PyNaCl required.")

def generate_keypair():
    sk = SigningKey(os.urandom(32))
    return sk, sk.encode().hex(), sk.verify_key.encode().hex()

def sign_bytes(signing_key: SigningKey, message: bytes) -> str:
    return signing_key.sign(message).signature.hex()

def verify_signature(public_key_hex: str, signature_hex: str, message: bytes) -> bool:
    try:
        vk = VerifyKey(bytes.fromhex(public_key_hex))
        vk.verify(bytes.fromhex(signature_hex) + message)
        return True
    except Exception:
        return False

@dataclass
class ConsequenceRequest:
    execution_id: str
    operation_id: str
    epoch: int
    payload: str
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {"execution_id": self.execution_id, "operation_id": self.operation_id, "epoch": self.epoch, "payload": self.payload}
        return json.dumps(d, sort_keys=True).encode("utf-8")
    def to_dict(self): return asdict(self)

@dataclass
class ConsequencePermit:
    execution_id: str
    operation_id: str
    payload: str
    authority_signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {"execution_id": self.execution_id, "operation_id": self.operation_id, "payload": self.payload}
        return json.dumps(d, sort_keys=True).encode("utf-8")
    def to_dict(self): return asdict(self)
