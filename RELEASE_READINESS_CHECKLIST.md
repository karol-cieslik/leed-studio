# LEED Studio 0.11.1 — Release-readiness checklist

This checklist distinguishes repository preparation from release acceptance. A checked-in configuration is not evidence that a release build has passed.

## Repository hygiene

- [x] Version metadata agrees on 0.11.1 (`pyproject.toml`, `leed_studio/__init__.py`, wheel metadata).
- [x] README installer output filename corrected to `LEED-Studio-Setup-0.11.1.exe`.
- [x] Generated Python/build/test artifacts excluded from a normal source repository via `.gitignore`.
- [x] Scientific limitations and outstanding experimental validation disclosed in README.
- [x] Review historical audit documents for version drift; README now identifies them as historical records, not current-release acceptance evidence.
- [ ] Establish Git repository and verify maintainer identity / attribution before first public push.

## Automated acceptance

- [x] Linux regression baseline: `python -m pytest -q -ra` — 47 passed, 1 skipped (Qt dependency unavailable).
- [x] `python -m compileall -q leed_studio tests tools`.
- [x] `python -m leed_studio --self-test-core`.
- [ ] Run tests in a clean environment with declared dependencies installed.
- [ ] Run `.github/workflows/windows-build.yml` on a Windows GitHub Actions runner.
- [ ] Confirm portable ZIP and installer are produced and downloadable.
- [ ] Review `WINDOWS_ACCEPTANCE_TESTS.txt` from the successful Windows run.
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
4. Require the Windows workflow to pass; attach its portable ZIP, installer and test record.
5. Include the scientific limitations and identify the release as an exploratory prototype until experimental validation is complete.
