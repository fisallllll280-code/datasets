"""Narrow adapter boundary around Hugging Face Datasets.

The library is an ingestion/transformation engine, not an authority source.
Remote loading is disabled by default and requires an explicit policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .policy import DatasetPolicy


class DatasetAdmissionError(RuntimeError):
    """Raised when a request violates the adapter policy."""


@dataclass(frozen=True)
class DatasetLoadRequest:
    builder: str
    source: str
    revision: str | None = None
    config_name: str | None = None
    split: str | None = None
    streaming: bool = False
    local: bool = True


class HuggingFaceDatasetsAdapter:
    def __init__(self, policy: DatasetPolicy):
        self._policy = policy

    def load(self, request: DatasetLoadRequest) -> Any:
        errors = self._policy.validate_request(
            builder=request.builder,
            source=request.source,
            revision=request.revision,
            local=request.local,
        )
        if errors:
            raise DatasetAdmissionError(";".join(errors))
        if request.streaming and request.local is False:
            # Streaming is allowed only after the remote source has passed the same
            # explicit allowlist and pinned-revision checks as any other remote load.
            pass

        try:
            from datasets import load_dataset
        except ImportError as exc:
            raise DatasetAdmissionError(
                "huggingface_datasets_dependency_missing: install a compatible datasets version"
            ) from exc

        kwargs: dict[str, Any] = {
            "path": request.builder,
            "split": request.split,
            "streaming": request.streaming,
        }
        if request.config_name is not None:
            kwargs["name"] = request.config_name
        if request.revision is not None:
            kwargs["revision"] = request.revision

        if request.local:
            # Local paths are constrained by policy. The builder receives a path,
            # not executable instructions supplied by the dataset content.
            kwargs["data_files"] = request.source
        else:
            kwargs["path"] = request.source

        return load_dataset(**kwargs)
