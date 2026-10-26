# LEED Studio — development roadmap and historical map

**Current as of:** 26 October 2026, `main` commit `cde29ea`, source version `0.11.1`.  
**Meaning of checked boxes:** completed with the stated evidence, not a declaration of scientific accuracy. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the detailed inventory.

## What has already been achieved

- [x] A Python/Qt desktop codebase with dockable scientific-image workspace and one-spot workflow.
- [x] Gaussian fitting, tracking, aperture/annulus intensity measurement, basic calibrations and mask handling in source, with synthetic regression tests.
- [x] `.leedproj` save/load and CSV/JSON outputs in source.
- [x] A documented historical 0.11.1 Python-test baseline: **47 passed, 1 skipped** on 14 October (Qt skipped). **Current uploaded `main` is not known green**: at least two packaging tests assert CI steps missing from today's shorter workflow.
- [x] The current `main` source built under Windows in GitHub Actions on 15 October; the `LEED-Studio-Windows` artifact was uploaded.
- [ ] A **fully tested** downloadable Windows application/installer accepted on a real desktop.
- [ ] Numerical comparison with experimental Fe₂O₃ Spot Tracker reference data.
- [ ] Publication-grade scientific validation.

## Priority 1 — establish a genuine colleague-testable Windows build

**Why first:** getting a successful PyInstaller artifact is progress, but no recorded run of the frozen executable currently proves a colleague can operate it.

- [ ] Download [the latest successful artifact](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) and run the bundled EXE on Windows.
- [ ] Verify launch, sample opening, selection, Gaussian fit, I(E), warnings, project save/reopen and CSV export.
- [ ] Check high-DPI, docks, file dialogs, error handling and real TIFF loading.
- [ ] Resolve the mismatch between `tests/test_release_packaging.py` and the short workflow, then add `pytest`, `--self-test-core` and `--self-test-gui` to CI; run the **frozen** EXE self-tests after PyInstaller. Retain logs as artifacts.
- [ ] Decide whether the **installer** is required for a colleague beta. If yes, add Inno Setup build and install/uninstall tests; otherwise label the package **portable**, not “installer”.
- [ ] After acceptance, publish a clearly labeled **experimental beta** Release with the tested artifact, source, limitations and exact tested commit.

**Acceptance evidence:** a green workflow with explicit test/frozen-EXE steps, a downloadable tested package, and a completed [manual acceptance checklist](WINDOWS_MANUAL_ACCEPTANCE_CHECKLIST.md). A green *build-only* workflow is insufficient.

## Priority 2 — reconcile the open beginner experience

- [ ] Review [PR #1](https://github.com/karol-cieslik/leed-studio/pull/1), which is **unmerged** and adds auto-loaded simulated practice data, `BEGINNER_WALKTHROUGH.md` and README changes.
- [ ] Run current tests on the PR branch and interactively verify first launch, repeat launch, new raw data, and whether demo energy confirmation ever leaks into real-data sessions.
- [ ] Merge only after review; resolve README/documentation conflicts with this audit if needed.
- [ ] Once merged, update [PROJECT_STATUS.md](PROJECT_STATUS.md) and the user guide to say “on `main`”.

**Acceptance evidence:** merged PR commit, passing tests and a first-run Windows check.

## Priority 3 — real scientific validation

- [ ] Download the public [TU Wien Fe₂O₃ LEED-I(V) dataset](https://doi.org/10.48436/hgg42-xss85) and matching reference x/y outputs; record source, file names and checksums.
- [ ] Verify archive/frame ordering, x/y CSV orientation, beam-row choice, energies and coordinates.
- [ ] Run `tools/benchmark_tuwien_fe2o3.py` on several independent beams (easy isolated spots, weak spots, neighbours, problematic frames), not just the synthetic fixture.
- [ ] Report RMSE, median and high-percentile coordinate error, lost frames and unflagged beam switches; investigate failures and preserve commands/results.
- [ ] Separately define/match intensity background, integration radius, flat-field, beam-tail and normalization methods before claiming intensity agreement with ViPErLEED.
- [ ] Repeat on additional acquisitions and document reliability/uncertainty before a scientific software manuscript.

**Acceptance evidence:** publicly reproducible real-data metrics with limitations and comparison to the appropriate reference. The earlier **0.0054 px** figure is *synthetic only*.

## Later engineering work (not yet done)

- [ ] Robust multi-candidate tracking, overlap/crossing disambiguation and explicit ambiguous-identity states.
- [ ] Multi-beam list/batch analysis, indexing and symmetry-equivalent beam handling.
- [ ] Instrument metadata and arbitrary energy vectors (rather than fixed first-energy + constant step).
- [ ] Lazy stack readers, background workers, progress/cancel for large datasets.
- [ ] Uncertainty calibration and stronger quality diagnostics.
- [ ] Schema migration, autosave/recovery, undo/redo and tests for interrupted saving.
- [ ] Better real-world UX feedback from colleagues and a documented reproducibility package.

## What the historical filenames mean

| Document | Period/version | How to use it now |
|---|---|---|
| `TECHNICAL_AUDIT.md`, `PUBLIC_DATA_BENCHMARK.md` | 0.9.0 | Historical adverse-test results and Fe₂O₃ benchmark plan; **not** experimental validation |
| `VALIDATION_RESULTS.md` | 0.10.0 | Historical Python checks |
| `GUI_RELEASE_AUDIT_0_11_0.md` | 0.11.0 | Implementation history of dockable GUI/packaging |
| `VALIDATION_RESULTS_0_11_1.md`, `RELEASE_NOTES_DRAFT_0_11_1.md` | 0.11.1 | Historical source check and draft notes; revalidate for new code |
| `STAGE8_REVIEW_CHECKLIST.md`, `GITHUB_MOBILE_HANDOFF.md`, `STAGE9_RELEASE_CANDIDATE_STATUS.md`, `REPOSITORY_HANDOFF.md` | Before/around first GitHub upload | Handover provenance; references to local backups, logs, issue templates and release manifests may not exist in GitHub |
| `CHANGELOG.md` | Version intent and work summary | Historical intentions, **not proof** that today's CI executes all listed stages |
| `PROJECT_STATUS.md` | Current audited default branch | **First place to check what is actually present/verified** |
| `DEVELOPER_GUIDE.md` | Current architecture | How source, algorithms, tests, project files and packaging work |
| `DOCUMENTATION_INDEX.md` | Current navigation | Which file to read for which question |

## A brief actual GitHub timeline

- **14 October 2026:** Stage/audit documents record 0.11.1 source baseline, 47 passing tests and one skipped GUI test; experimental and Windows desktop acceptance remain open.
- **15 October 2026:** Repository initial upload plus three `main` commits; three Windows build-only Actions jobs pass. Latest source commit `cde29ea`.
- **18 October 2026:** Four commits on `beginner-first-run-experience` branch introduce first-launch changes; PR #1 remains open.
- **26 October 2026:** This audit differentiates source implementation, actual GitHub CI steps, pending PR, historical reports, and scientific validation gaps. Documentation-only changes are proposed separately for review.

Earlier 0.8–0.11 development is documented in the supplied historical files but is **not individually reconstructible from the four `main` commits**.

## Rule for future status updates

Do not write “done” based only on a source file, checkmark in an old document, or an intended CI step. For each acceptance gate, attach an exact commit, dated command or run, output/artifact and environment. Keep failed and not-run work visible.
