import os
import sys
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Optional, List

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    raise RuntimeError("PyNaCl is mandatory for Veklom Discovery execution.")

@dataclass
class DelegationCertificate:
    parent_id: str
    child_id: str
    depth: int
    parent_public_key: str
    child_public_key: str
    ceiling: List[str]
    issue_timestamp: str
    parent_signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "depth": self.depth,
            "parent_public_key": self.parent_public_key,
            "child_public_key": self.child_public_key,
            "ceiling": sorted(self.ceiling),
            "issue_timestamp": self.issue_timestamp,
        }
        return json.dumps(d, sort_keys=True).encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'DelegationCertificate':
        return cls(**d)

@dataclass
class RecursiveConsequenceRequest:
    execution_id: str
    epoch: int
    holder_id: str
    operation_id: str
    target_resource: str
    signing_key_public: str
    state_root: str
    evidence_head: str
    payload_digest: str
    delegation_chain: List[dict] # List of DelegationCertificate dicts
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        d = {
            "execution_id": self.execution_id,
            "epoch": self.epoch,
            "holder_id": self.holder_id,
            "operation_id": self.operation_id,
            "target_resource": self.target_resource,
            "signing_key_public": self.signing_key_public,
            "state_root": self.state_root,
            "evidence_head": self.evidence_head,
            "payload_digest": self.payload_digest,
            "delegation_chain": self.delegation_chain,
        }
        return json.dumps(d, sort_keys=True).encode("utf-8")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'RecursiveConsequenceRequest':
        return cls(**d)
