# VAIXLNS Dataset Fabric v1

## Purpose

Provide a reviewable, fail-closed boundary around the Hugging Face `datasets`
library. The library remains responsible for loading and transforming datasets;
this adapter provides request policy checks and deterministic local-file
integrity receipts. The adapter is not the sovereign authority.

## Repository boundary

This integration is intentionally additive. It does not rewrite
`src/datasets/` and does not claim to be wired into the VAIXLNS or NEXENT
runtime. Cross-repository wiring is a later integration gate.

## Components

- `vaixlns_dataset_fabric/contracts.py`: typed identity, manifest, receipt,
  and promotion-decision contracts.
- `policy.py`: explicit builder/source/revision policy; remote access denied
  by default.
- `adapter.py`: narrow optional wrapper around `datasets.load_dataset`.
- `verify.py`: SHA-256 inventory, size limits, expected-digest checks, and
  symlink rejection for local regular files.
- `tests/test_vaixlns_dataset_fabric.py`: contract and adversarial boundary tests.

## Trust and evidence semantics

- A content digest establishes byte-level identity for the bytes hashed. It does
  not establish authenticity, quality, legality, or suitability.
- Dataset identity, content digest, and execution digest are distinct concepts.
- Dataset content is untrusted data, never an instruction to the host or kernel.
- A successful integrity receipt is not semantic validation and not authorization.
- The adapter cannot authorize promotion. The VAIXLNS authority layer must make
  that decision independently.
- Remote loading is disabled by default. Enabling it requires explicit policy,
  an allowlisted repository identifier, and a pinned revision.
- Local file verification is not an OS sandbox. Do not load untrusted executable
  code or enable remote code execution in a privileged process.

## Known limitations

- This v1 does not yet inspect the full Hugging Face Hub revision/commit metadata.
- It does not guarantee deterministic transformation output across hardware,
  library versions, or nondeterministic transforms.
- It does not enforce licenses or establish source authenticity.
- The adapter currently provides the minimal load boundary, not a complete
  dataset catalog or NEXENT/VX bridge.
- Policy root protection, signed receipts, atomic persistence, and runtime
  sandbox enforcement remain separate requirements.

## Local checks

Run:

```bash
python -m pytest -q tests/test_vaixlns_dataset_fabric.py
```

The repository CI workflow is the authoritative source for the tested commit.
A code file or local test result alone does not mean the system is production-ready.
