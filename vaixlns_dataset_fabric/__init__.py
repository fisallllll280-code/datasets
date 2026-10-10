"""VAIXLNS Dataset Fabric: proof-gated integration for Hugging Face Datasets."""

from .contracts import (
    DatasetIdentity,
    DatasetManifest,
    PromotionDecision,
    VerificationReceipt,
)
from .policy import DatasetPolicy
from .verify import verify_local_files

__all__ = [
    "DatasetIdentity",
    "DatasetManifest",
    "DatasetPolicy",
    "PromotionDecision",
    "VerificationReceipt",
    "verify_local_files",
]
