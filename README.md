# LEED Studio 0.11.1

LEED Studio is a desktop prototype for exploring **low-energy electron diffraction (LEED)** pictures and image stacks. It lets you select **one** diffraction spot, examine its shape, follow it across frames, estimate an intensity-versus-energy **I(E)** curve, inspect warnings, save work and export results.

**In plain language:** this is real software with implemented scientific-analysis methods, **not yet a validated measurement tool or a fully tested public Windows release**.

> **Where should I start?** [What is finished and what is not?](PROJECT_STATUS.md) · [What to do next?](ROADMAP.md) · [How the code works](DEVELOPER_GUIDE.md) · [Documentation map](DOCUMENTATION_INDEX.md)

## Try it in four steps

1. Start the application and click **Try example** to load the included *simulated* image stack (or **Open data…** for your own picture/TIFF stack).
2. Click near the centre of a visible diffraction spot.
3. Choose **Measure spot profile** to fit one frame; or enter and explicitly confirm the **real** energy start/step, then choose **Measure intensity vs energy** for the stack.
4. Inspect the fit residual, I(E) curve, quality flags and questionable frames. Save a `.leedproj` project; export CSV plus its settings sidecar after checking results.

The example is synthetic practice data—not an experimental benchmark. For a fuller explanation of correction options, coordinates, caveats and result meanings, read the [software overview and user manual](SOFTWARE_OVERVIEW_AND_USER_MANUAL.md).

**Note on first launch:** the current `main` branch requires you to click **Try example**. An automatic first-launch example and beginner walkthrough are proposed in [open PR #1](https://github.com/karol-cieslik/leed-studio/pull/1); they are **not merged**.

## What exists today?

| Area | Short answer |
|---|---|
| Desktop UI | Dockable Qt/pyqtgraph workspace, image viewer, curve/table and residual panel exist in source |
| Analysis | Single-spot Gaussian fit, local tracking, aperture/annulus intensity and basic corrections exist; synthetic tests cover core cases |
| Persistence | `.leedproj` project archives, CSV and provenance JSON sidecars exist |
| Windows | [GitHub Actions successfully built](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) a portable executable artifact |
| Still missing | Frozen executable acceptance, verified installer, full current CI test pass, interactive Windows checks and experimental-data accuracy validation |
| Future scope | Robust overlapping/multi-beam tracking, indexing, large-stack streaming, broader calibration and scientific reference benchmarking |

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the evidence behind each entry and the distinction between “code present”, “historically tested” and “actually verified”.

## Download / run

### Windows portable build (unverified interactive behavior)

Open [the latest successful Windows Actions run](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) and download **LEED-Studio-Windows** under Artifacts (GitHub sign-in may be required). Extract the artifact; look inside its `dist` contents for the **LEED Studio** folder and `LEED Studio.exe`. Keep the accompanying `_internal` files with it.

The packaging job ran successfully on 15 October 2026, but **did not execute the frozen EXE or perform GUI tests**. Treat the download as an experimental build, not an accepted release. There is no confirmed published installer or GitHub Release.

### Run from source

Use Python 3.11 or 3.12 with the declared dependencies. From a source checkout:

```powershell
python -m pip install -e ".[dev]"
python -m leed_studio
```

On Windows, `install_windows.ps1` sets up a virtual environment and starts the app; `run_windows.bat` starts it later. See [WINDOWS_GUI_GUIDE.md](WINDOWS_GUI_GUIDE.md) for UI and packaging instructions.

## What has actually been tested?

An older 14 October 2026 source audit reported **47 passed, 1 skipped** (Qt unavailable). This is historical evidence, **not a rerun of the present GitHub checkout**. In fact, some packaging test assertions currently expect installer/self-test CI steps that are absent from the checked-in workflow, so a new passing result must not be assumed.

The 15 October [Windows Actions run](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) installed dependencies and built/uploaded the portable app. Its current workflow did **not** run tests, the frozen app, or an installer. Consult [PROJECT_STATUS.md](PROJECT_STATUS.md) and [ROADMAP.md](ROADMAP.md) before describing release readiness.

## Scientific limits

LEED Studio is **exploratory** and not a validated replacement for ViPErLEED Spot Tracker. The proposed real experimental comparison uses the [TU Wien Fe₂O₃ LEED-I(V) dataset](https://doi.org/10.48436/hgg42-xss85), but that comparison has not been completed. A previously reported 0.0054-pixel tracking RMSE came from a *synthetic* fixture, not this experimental dataset. Do not rely on LEED Studio measurements for publication without independent validation.

The dockable interface takes **interaction inspiration from Gwyddion**; LEED Studio is an independent implementation, not a Gwyddion fork. ViPErLEED is a comparison reference, not a claimed equivalent.

## For future readers / contributors

- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md):** where to find each guide.
- **[PROJECT_STATUS.md](PROJECT_STATUS.md):** grounded inventory of implemented, unverified, PR-only and missing work.
- **[ROADMAP.md](ROADMAP.md):** prioritized work with explicit acceptance criteria.
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md):** architecture, algorithms, source file map, tests and data formats.
- **[SOFTWARE_OVERVIEW_AND_USER_MANUAL.md](SOFTWARE_OVERVIEW_AND_USER_MANUAL.md):** detailed user guide and interpretation warnings.
- **[CHANGELOG.md](CHANGELOG.md):** historical development record; current CI behavior is defined by the actual workflow.

License: GPL-3.0-or-later ([LICENSE](LICENSE)). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [CREDITS.md](CREDITS.md) for dependencies, project direction and AI-assisted development provenance.
