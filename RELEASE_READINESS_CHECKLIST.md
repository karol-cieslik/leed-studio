# LEED Studio 0.11.1 — Release-readiness checklist

*Reconciled against GitHub `main` on 26 October 2026. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for evidence and [ROADMAP.md](ROADMAP.md) for priorities.*

This checklist distinguishes repository preparation from release acceptance. A checked-in configuration is not evidence that a release build has passed.

## Repository hygiene

- [x] Version metadata agrees on 0.11.1 (`pyproject.toml`, `leed_studio/__init__.py`, wheel metadata).
- [x] README installer output filename corrected to `LEED-Studio-Setup-0.11.1.exe`.
- [ ] Add/verify `.gitignore` in the uploaded GitHub repository (not present in the audited `main` tree); exclude Python/build/test artifacts.
- [x] Scientific limitations and outstanding experimental validation disclosed in README.
- [x] Review historical audit documents for version drift; README now identifies them as historical records, not current-release acceptance evidence.
- [x] Public GitHub repository created and commits attributed to `karol-cieslik` (15 October 2026). Maintainer should still review attribution and licence disclosures.

## Automated acceptance

- [x] **Historical (14 October) source** baseline: `python -m pytest -q -ra` — 47 passed, 1 skipped (Qt dependency unavailable).
- [ ] Rerun on **current uploaded `main`**. At least two assertions in `tests/test_release_packaging.py` currently require workflow strings/steps absent from `.github/workflows/windows-build.yml`; reconcile the mismatch, then record exact current results.
- [x] `python -m compileall -q leed_studio tests tools`.
- [x] `python -m leed_studio --self-test-core`.
- [ ] Run tests in a clean environment with declared dependencies installed.
- [x] **Build-only CI:** `.github/workflows/windows-build.yml` succeeded on Windows, [run 38743872970](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970), 15 October 2026.
- [ ] **Acceptance CI:** add/run Python tests, packaged `--self-test-core`/`--self-test-gui`, normal EXE launch checks, and installer steps if wanted; current workflow omits them.
- [x] Portable Windows artifact (`LEED-Studio-Windows`) uploaded by build-only workflow; contents have not been manually accepted.
- [ ] Build and verify an Inno Setup **installer** separately if needed; no installer artifact was uploaded in the audited run.
- [ ] Produce/review a Windows acceptance log. `WINDOWS_ACCEPTANCE_TESTS.txt` is not produced by the current workflow.
- [ ] Perform a manual interactive Windows GUI check (display scaling, dock dragging, opening/saving projects, exports).

## Scientific acceptance

- [ ] Download and verify the TU Wien Fe₂O₃ LEED-I(V) dataset and reference Spot Tracker results.
- [ ] Run `tools/benchmark_tuwien_fe2o3.py` against the real data and retain exact command, dataset version/checksum and output.
- [ ] Report coordinate-error metrics, tracking failures and frame alignment.
- [ ] Keep synthetic and experimental metrics explicitly separate.
- [ ] Do not claim equivalence to ViPErLEED or publication-grade accuracy without evidence.

## Before publishing a GitHub Release

1. Review the diff and ensure no user data, credentials, local paths or generated caches are committed.
2. Confirm licence, third-party notices and attribution are present.
3. Ensure the tag matches package metadata (`v0.11.1` for this snapshot).
4. Require Windows **runtime/acceptance** checks, not merely build success; attach the verified portable artifact, optional installer (if built), and test record.
5. Include the scientific limitations and identify the release as an exploratory prototype until experimental validation is complete.
