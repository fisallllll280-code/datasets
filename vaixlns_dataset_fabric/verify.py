"""Deterministic local-file verification helpers; no dataset code is executed."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

from .contracts import VerificationReceipt


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_local_files(
    paths: Iterable[str | os.PathLike[str]],
    *,
    subject_digest: str,
    max_file_bytes: int,
    max_total_bytes: int,
    expected_digests: dict[str, str] | None = None,
) -> VerificationReceipt:
    """Inventory regular files and verify size/digest constraints.

    Symlinks are rejected. This function does not prove the provenance or safety
    of file contents and deliberately does not parse or execute them.
    """
    expected_digests = expected_digests or {}
    failures: list[str] = []
    inventory: list[dict[str, object]] = []
    total = 0

    for raw in sorted((Path(p) for p in paths), key=lambda p: str(p)):
        try:
            if raw.is_symlink():
                failures.append(f"symlink_rejected:{raw}")
                continue
            resolved = raw.resolve(strict=True)
            if not resolved.is_file():
                failures.append(f"not_regular_file:{raw}")
                continue
            size = resolved.stat().st_size
            total += size
            if size > max_file_bytes:
                failures.append(f"file_size_limit_exceeded:{raw}")
            digest = _sha256_file(resolved)
            expected = expected_digests.get(str(raw))
            if expected is not None and digest != expected:
                failures.append(f"digest_mismatch:{raw}")
            inventory.append({"path": str(raw), "size": size, "sha256": digest})
        except (OSError, RuntimeError) as exc:
            failures.append(f"file_unavailable:{raw}:{type(exc).__name__}")

    if total > max_total_bytes:
        failures.append("total_size_limit_exceeded")
    status = "FAIL" if failures else ("PASS" if inventory else "UNKNOWN")
    return VerificationReceipt(
        check_id="local-file-integrity-v1",
        status=status,
        subject_digest=subject_digest,
        evidence={"files": inventory, "total_bytes": total, "failures": failures},
        reason=";".join(failures) if failures else ("files_checked" if inventory else "no_files_checked"),
    )
