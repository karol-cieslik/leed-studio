# LEED Studio 0.11.1 — Stage 9 release-candidate status

**Date:** 2026-10-14  
**Purpose:** Freeze a reviewable 0.11.1 source candidate, reconcile documentation navigation/version drift, and record release gates.  
**Functional code changes:** None.

## Source freeze and preservation

- Candidate was copied from the Stage 8 source snapshot into a new Stage 9 working directory.
- The Stage 8 delivery archive is preserved in `backup/LEED_Studio_Stage8_Delivery_pre_stage9.zip`.
- Only README documentation navigation and the release checklist's historical-documentation review status were updated.
- Application modules, analysis algorithms, tests, dependency declarations, packaging scripts, and CI workflow were not modified.
- A SHA-256 manifest for every source-candidate file is provided in `release/SOURCE_MANIFEST.json`.

## Documentation reconciliation

The README now distinguishes current 0.11.1 status documents from historical records for 0.9.0, 0.10.0, and 0.11.0. Historical documents are retained for provenance, not presented as current acceptance evidence.

## Reproduced checks

See `logs/pytest.log`, `logs/compile.log`, and `logs/core.log` for command output. GUI smoke testing remains skipped because PySide6 is unavailable in this Linux environment.

## Release gates still open

1. Run `.github/workflows/windows-build.yml` on a Windows GitHub Actions runner and inspect the portable ZIP, installer, and acceptance log.
2. Complete interactive Windows acceptance using `WINDOWS_MANUAL_ACCEPTANCE_CHECKLIST.md`.
3. Download the TU Wien Fe2O3 LEED-I(V) dataset and matching reference Spot Tracker outputs; record checksums and run `tools/benchmark_tuwien_fe2o3.py`.
4. Keep coordinate accuracy, intensity equivalence, and any ViPErLEED comparison unclaimed until measured with appropriate reference data.
5. Verify Git author identity and attribution before first public push. No repository was pushed and no release/tag was created by this stage.

## Decision

**Source candidate frozen for review; not release-accepted.** This candidate is suitable for repository review and CI execution, but must not be described as a verified Windows release or scientifically validated software.
