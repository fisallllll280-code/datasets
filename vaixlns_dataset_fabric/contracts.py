"""Stable, serialization-friendly contracts for dataset admission.

Digests identify the exact canonicalized record or bytes observed; they do not
prove source authenticity, licensing, semantic correctness, or permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DatasetIdentity:
    source_uri: str
    source_revision: str
    content_digest: str
    builder: str
    config_name: str | None = None
    split: str | None = None

    @property
    def identity_digest(self) -> str:
        return sha256_text(canonical_json(asdict(self)))


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    identity: DatasetIdentity
    schema: dict[str, str] = field(default_factory=dict)
    license_id: str | None = None
    transformations: tuple[dict[str, Any], ...] = ()
    dependency_lock_digest: str | None = None


@dataclass(frozen=True)
class VerificationReceipt:
    check_id: str
    status: str
    subject_digest: str
    evidence: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("status must be PASS, FAIL, or UNKNOWN")
        if not self.check_id or not self.subject_digest:
            raise ValueError("check_id and subject_digest are required")


@dataclass(frozen=True)
class PromotionDecision:
    state: str
    authorized: bool
    reasons: tuple[str, ...]
    receipt_digests: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in {
            "QUARANTINED", "REJECTED", "VERIFIED_PENDING_AUTHORITY", "AUTHORIZED"
        }:
            raise ValueError("unsupported promotion state")
        # This adapter is not an authority. It must never self-authorize a dataset.
        if self.authorized:
            raise ValueError("dataset adapter cannot issue sovereign authorization")
