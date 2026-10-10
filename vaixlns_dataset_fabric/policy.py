"""Fail-closed policy for the dataset adapter."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatasetPolicy:
    allowed_builders: frozenset[str] = frozenset({"csv", "json", "parquet", "text"})
    allowed_local_roots: tuple[str, ...] = ()
    allowed_remote_repositories: frozenset[str] = frozenset()
    allow_remote: bool = False
    require_pinned_revision: bool = True
    max_file_bytes: int = 512 * 1024 * 1024
    max_total_bytes: int = 2 * 1024 * 1024 * 1024
    require_license_metadata: bool = False
    required_columns: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def validate_request(
        self,
        *,
        builder: str,
        source: str,
        revision: str | None,
        local: bool,
    ) -> tuple[str, ...]:
        errors: list[str] = []
        if builder not in self.allowed_builders:
            errors.append(f"builder_not_allowed:{builder}")
        if local:
            if not self.allowed_local_roots:
                errors.append("no_local_roots_configured")
            elif not any(
                source == root or source.startswith(root.rstrip("/") + "/")
                for root in self.allowed_local_roots
            ):
                errors.append("local_source_outside_allowed_roots")
        else:
            if not self.allow_remote:
                errors.append("remote_sources_disabled")
            if source not in self.allowed_remote_repositories:
                errors.append("remote_repository_not_allowlisted")
            if self.require_pinned_revision and not revision:
                errors.append("remote_revision_required")
        return tuple(errors)
