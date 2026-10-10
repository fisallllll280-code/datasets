from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from vaixlns_dataset_fabric.adapter import (
    DatasetAdmissionError,
    DatasetLoadRequest,
    HuggingFaceDatasetsAdapter,
)
from vaixlns_dataset_fabric.contracts import (
    DatasetIdentity,
    PromotionDecision,
    VerificationReceipt,
)
from vaixlns_dataset_fabric.policy import DatasetPolicy
from vaixlns_dataset_fabric.verify import verify_local_files


def test_identity_digest_is_deterministic():
    identity = DatasetIdentity("file:///data.csv", "git:abc123", "a" * 64, "csv")
    assert identity.identity_digest == identity.identity_digest
    assert len(identity.identity_digest) == 64


def test_policy_rejects_remote_by_default():
    policy = DatasetPolicy()
    errors = policy.validate_request(
        builder="csv", source="org/data", revision="abc123", local=False
    )
    assert "remote_sources_disabled" in errors
    assert "remote_repository_not_allowlisted" in errors


def test_policy_requires_revision_for_allowlisted_remote():
    policy = DatasetPolicy(
        allow_remote=True,
        allowed_remote_repositories=frozenset({"org/data"}),
    )
    errors = policy.validate_request(
        builder="csv", source="org/data", revision=None, local=False
    )
    assert "remote_revision_required" in errors


def test_adapter_fails_before_import_for_disallowed_request():
    adapter = HuggingFaceDatasetsAdapter(DatasetPolicy())
    with pytest.raises(DatasetAdmissionError, match="remote_sources_disabled"):
        adapter.load(DatasetLoadRequest("csv", "org/data", revision="abc123", local=False))


def test_local_file_inventory_and_digest(tmp_path: Path):
    file = tmp_path / "sample.csv"
    file.write_text("id,value\n1,ok\n", encoding="utf-8")
    expected = hashlib.sha256(file.read_bytes()).hexdigest()
    receipt = verify_local_files(
        [file],
        subject_digest="subject-v1",
        max_file_bytes=1024,
        max_total_bytes=2048,
        expected_digests={str(file): expected},
    )
    assert receipt.status == "PASS"
    assert receipt.evidence["files"][0]["sha256"] == expected


def test_changed_file_is_detected(tmp_path: Path):
    file = tmp_path / "sample.csv"
    file.write_text("before", encoding="utf-8")
    receipt = verify_local_files(
        [file],
        subject_digest="subject-v1",
        max_file_bytes=1024,
        max_total_bytes=2048,
        expected_digests={str(file): "0" * 64},
    )
    assert receipt.status == "FAIL"
    assert "digest_mismatch" in receipt.reason


def test_symlink_is_rejected(tmp_path: Path):
    target = tmp_path / "target.csv"
    target.write_text("id\n1\n", encoding="utf-8")
    link = tmp_path / "link.csv"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported in this environment")
    receipt = verify_local_files(
        [link],
        subject_digest="subject-v1",
        max_file_bytes=1024,
        max_total_bytes=2048,
    )
    assert receipt.status == "FAIL"
    assert "symlink_rejected" in receipt.reason


def test_adapter_cannot_self_authorize():
    with pytest.raises(ValueError, match="cannot issue sovereign authorization"):
        PromotionDecision("AUTHORIZED", True, ("adapter cannot authorize",))


def test_receipt_rejects_unknown_status():
    with pytest.raises(ValueError, match="status must be"):
        VerificationReceipt("check", "TRUST_ME", "subject")
