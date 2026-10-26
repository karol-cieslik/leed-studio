# LEED Studio — implementation and verification status

**Audit date:** 26 October 2026  
**Repository:** [karol-cieslik/leed-studio](https://github.com/karol-cieslik/leed-studio)  
**Audited default branch:** `main`, commit [`cde29ea`](https://github.com/karol-cieslik/leed-studio/commit/cde29ea6ccc7ed8a503e7172bd33bba96aa12c39) (15 October 2026)  
**Source version:** `0.11.1` (`pyproject.toml`, `leed_studio/__init__.py`)

> **In one sentence:** LEED Studio is a real, functional-in-source research prototype for inspecting LEED image stacks and measuring a *single selected spot*; a Windows executable has been built, but interactive behavior and experimental accuracy have **not** been accepted or scientifically validated.

## How to read the statuses

- **Implemented in source:** code is present on `main`; this alone does not prove that it works on every computer or dataset.
- **Tested previously:** a named test and result are recorded in historical reports; the test was not rerun for this audit.
- **Windows build verified:** GitHub Actions completed a Windows packaging job and uploaded an artifact. This is narrower than GUI acceptance.
- **In open PR:** code exists on another branch, but is not in `main`.
- **Not implemented / not verified:** explicitly missing, or evidence of successful execution was not found. These are different claims.

## Feature inventory for `main`

| Capability | State | Source and evidence | Important boundary |
|---|---|---|---|
| Open grayscale pictures, TIFFs and multipage TIFF stacks | **Implemented in source** | `leed_studio/analysis.py:load_image_stack`, `leed_studio/app.py:_load_image_path`; input tests | Detector-specific formats/metadata and unusual TIFF axes may fail |
| Central image viewer, frame slider, histogram/contrast, cursor readout and spot click | **Implemented in source** | `leed_studio/app.py:ImagePanel`, `MainWindow` | Current interactive behavior has not been manually accepted on Windows |
| Dockable project, tools, curve and residual panes; beginner mode; saved layout | **Implemented in source** | `leed_studio/app.py:MainWindow`; optional `tests/test_gui_smoke.py` | Dock dragging, scaling and persistence have no documented live manual pass |
| Elliptical-Gaussian spot-profile fitting, residual image, fit flags | **Implemented; synthetic tests** | `leed_studio/analysis.py:fit_spot`, `tests/test_analysis.py` | A plausible fit is not independently confirmed experimental spot geometry |
| One-spot tracking in both directions from selected frame | **Implemented; synthetic tests** | `leed_studio/analysis.py:track_spot_series` | Nearest plausible local maximum plus centroid and motion gate, **not** full beam indexing/robust identity tracking |
| Circular-aperture, median-annulus, background-subtracted intensity per frame | **Implemented; synthetic tests** | `track_spot_series`, `save_series_csv` | Intensity definition is **not equivalent to ViPErLEED** |
| Manual energy start and fixed energy step, with explicit confirmation | **Implemented in GUI** | `leed_studio/app.py:run_series` and energy controls | No automatic detector-energy import or arbitrary/nonuniform energy axis |
| Dark, flat, dark-for-flat and mask inputs; average/framewise correction modes | **Implemented; synthetic tests** | `correct_image_stack`; related unit tests | Not a validated replica of instrument-/ViPErLEED-specific corrections |
| Per-frame results table, curve navigation and flagged-frame navigation | **Implemented in source** | `MainWindow.run_series`, `select_series_row`, `navigate_warning` | Full interactive verification is pending |
| Portable `.leedproj` save/open with arrays, settings and results | **Implemented; unit tests** | `leed_studio/project_io.py`, `tests/test_project_io.py` | Archive schema version 1; no migration/autosave system |
| Fit/I(E) CSV export and JSON metadata sidecar | **Implemented; unit tests for core output** | `save_fit_csv`, `save_series_csv`, GUI export handlers | Preserve exports and sidecars together; GUI save dialogs need manual checks |
| Core numerical self-test and optional Qt offscreen smoke test | **Implemented; historical test report** | `leed_studio/__main__.py`, `tests/` | Not run by the current GitHub workflow |
| Portable Windows application build | **Windows build succeeded** | [Actions run 38743872970](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) | Frozen program was **not** run in that job |
| Windows installer | **Recipe present; not verified** | `packaging/LEED-Studio.iss`, `build_windows.bat` | Current GitHub Actions does **not** produce an installer |
| First-run automatic practice example and beginner walkthrough | **Open PR only** | [PR #1](https://github.com/karol-cieslik/leed-studio/pull/1) | **Not on `main`** as of audit |
| Multi-beam tracking, crystallographic indexing, symmetry-equivalent averaging | **Not implemented** | No such workflow in current `app.py` / `analysis.py` | Currently one manually selected spot per measurement |
| Worker-based processing, progress/cancellation, lazy large-stack reader, autosave/undo | **Not implemented** | Synchronous in-memory processing paths | Large datasets may be slow or memory-heavy |
| Experimental reference-data validation | **Not completed** | `PUBLIC_DATA_BENCHMARK.md`, `VALIDATION_RESULTS_0_11_1.md` | No published experimental tracking-error or intensity-equivalence metrics |

## Actual test and Windows-build evidence

### Historical Python checks — 14 October 2026

`VALIDATION_RESULTS_0_11_1.md` records:

- `python -m compileall -q leed_studio tests tools` — **passed**.
- `python -m pytest -q -ra -p no:cacheprovider` — **47 passed, 1 skipped**.
- A source/wheel packaging and core numerical smoke-test path passed.
- The skipped test used Qt; PySide6/pyqtgraph were unavailable in that environment.

These are historical results on a source snapshot, **not tests rerun during this 26 October GitHub audit**. Importantly, **the uploaded `main` source no longer matches those reports**: `tests/test_release_packaging.py` has at least two tests that require installer artifact names, frozen-EXE tests and installer actions in `.github/workflows/windows-build.yml`, but those strings/steps are missing from today's shorter workflow. Those assertions therefore cannot pass as written on this audited `main` tree. This is a static source discrepancy, **not a fresh execution of pytest**. The current full test count is unknown until the suite is rerun. See [developer guide](DEVELOPER_GUIDE.md) to reproduce it.

### Actual GitHub Actions Windows job — 15 October 2026

The three `main` runs reported success; [the latest run](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) is for commit `cde29ea`. It performed:

1. Checkout on `windows-latest`.
2. Python 3.11 setup.
3. Installation of application and selected pinned build dependencies, followed by `pip check`.
4. `pyinstaller --noconfirm --clean LEED_Studio.spec`.
5. Upload of the `LEED-Studio-Windows` artifact (approximately 110 MB; not expired at audit).

**That is a successful Windows build.** The checked-in workflow does **not** run `pytest`, `--self-test-core`, `--self-test-gui`, the built `.exe`, an installer build, installation/uninstallation checks, or interactive desktop tests. The more ambitious sequence in older `README.md`, `SOFTWARE_OVERVIEW_AND_USER_MANUAL.md`, `WINDOWS_GUI_GUIDE.md`, `CHANGELOG.md` and old handoff reports describes an *earlier design/intention*, **not what the current checked-in workflow does**. A local `build_windows.bat` includes additional tests, but does not establish that they were run on GitHub.

**A GitHub Actions artifact is not a published GitHub Release.** No GitHub Release was found in the repository during this audit.

## Branches and unfinished work

| Branch | State | Meaning |
|---|---|---|
| `main` | Audited stable default, version 0.11.1 | Viewer, analysis, export, projects, Windows packaging source |
| `beginner-first-run-experience` | Four commits ahead of `main`; [PR #1](https://github.com/karol-cieslik/leed-studio/pull/1) open | Adds `BEGINNER_WALKTHROUGH.md`, revised README, and automatic first-launch simulated example; **not yet merged/tested by the current main-only workflow** |

Do not describe the PR-only automatic first-launch experience as a feature of `main`. On `main`, the user clicks **Try example** manually.

## Scientific interpretation

The tracker uses local peak selection, centroid refinement, a maximum-displacement check, a circular integration aperture and a median background annulus. It can flag bad frames and avoid some identity switches in controlled tests. This is useful *exploratory* analysis, but it does **not** implement full ViPErLEED Spot Tracker processing. The bundled `sample_drifting_stack.tif` is simulated.

The TU Wien Fe₂O₃ dataset is identified in [PUBLIC_DATA_BENCHMARK.md](PUBLIC_DATA_BENCHMARK.md), and `tools/benchmark_tuwien_fe2o3.py` is present. The reported **0.0054-pixel RMSE** came from a five-frame *synthetic fixture*, **not an experimental benchmark**. No experimental validation metrics are established.

## Documentation drift and missing handover material

- Older documents for versions **0.9.0, 0.10.0 and 0.11.0** are historical records. Preserve them, but never use them as current release certification.
- Some Stage 8/9 checklists refer to issue templates, `.gitignore`, `backup/`, `logs/`, `release/SOURCE_MANIFEST.json` or `WINDOWS_ACCEPTANCE_TESTS.txt` that are **not present in the audited `main` tree**. Their existence in an earlier local archive is not evidence that they were uploaded to GitHub.
- The current `main` history starts with the initial upload on 15 October; earlier staged local work is described in documents but is not individually traceable through this repository's Git commits.
- The workflow file in `.github/workflows/windows-build.yml` is the source of truth about current CI behavior.

## Next gates

1. [ ] Test the downloaded Windows artifact on a real Windows desktop; record startup, image/example open, fit, I(E), `.leedproj` round-trip, CSV export and dock interactions.
2. [ ] Reconcile the **two currently inconsistent packaging tests** with the intended CI requirements, then strengthen CI to run Python/Qt tests and frozen-app self-tests; optionally add an installer job. Update claims to match executed results.
3. [ ] Review/test [PR #1](https://github.com/karol-cieslik/leed-studio/pull/1) and merge if appropriate.
4. [ ] Run the public Fe₂O₃ *real experimental* coordinate benchmark with matching reference files, checksums and frame alignment.
5. [ ] Only after those checks consider a clearly labelled pre-release for colleagues; scientific equivalence/publication claims require further validation.

For prioritized steps and acceptance criteria, see [ROADMAP.md](ROADMAP.md). For the file/function map and reproducible developer commands, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

## Maintaining this page

After a meaningful code or workflow change, record: **date, branch, commit SHA, command or Actions run, result, environment, and what remains unverified**. Change a status from “implemented” to “verified” only when the evidence supports it. Never silently turn a proposed criterion into an achieved result.
