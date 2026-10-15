# LEED Studio 0.11.1

LEED Studio is a standalone LEED image-analysis prototype built with PySide6 and pyqtgraph. The GUI now uses a Gwyddion-inspired scientific workspace: a central image viewer with dockable project browser, tools/settings, I(E) curve and fit-residual panels.

**Scientific status:** exploratory research software, not a validated replacement for ViPErLEED Spot Tracker. Do not treat results as publication-grade measurements without independent validation against experimental reference data.

## Highlights in 0.11.1

- Dockable scientific workspace with persistent window/dock layout.
- Project data browser for image stack, calibration inputs, selected beam and analysis outputs.
- Linked curve/frame navigation and an image cursor readout showing pixel coordinates and working intensity.
- Beginner mode and resettable default workspace layout.
- Native-looking toolbar icons and panel visibility actions.
- Windows PyInstaller spec, local build script, Inno Setup installer recipe and GitHub Actions Windows build workflow.

## Quick start on Windows (source)

1. Install Python 3.11 or 3.12 from python.org.
2. Extract the complete source ZIP.
3. Run `install_windows.ps1` in PowerShell. To run later, double-click `run_windows.bat`.

## Build a standalone Windows executable

For a local build, install Python 3.12 and run `build_windows.bat`. This creates `dist\LEED Studio\LEED Studio.exe`. Install Inno Setup 6 and run `iscc packaging\LEED-Studio.iss` to create `release\LEED-Studio-Setup-0.11.1.exe`.

A GitHub Actions workflow (`.github/workflows/windows-build.yml`) is configured to run unit and offscreen Qt tests, build the Windows application, execute a frozen-EXE workflow self-test, check normal startup, build the installer, test installation/uninstallation, and upload artifacts. Run it manually from the Actions tab or push a version tag such as `v0.11.1`. These steps are **configured but not yet verified by a successful Windows run**; the workflow uploads artifacts and does not automatically publish a GitHub Release. A real interactive test on a Windows desktop is still recommended.

See `SOFTWARE_OVERVIEW_AND_USER_MANUAL.md` for the full software description, scientific basis, inspirations, limitations and user guide. See `WINDOWS_GUI_GUIDE.md` for dock controls and shortcuts.

## Documentation map and evidence status

- **Current release status:** `VALIDATION_RESULTS_0_11_1.md`, `RELEASE_READINESS_CHECKLIST.md`, and `WINDOWS_MANUAL_ACCEPTANCE_CHECKLIST.md`.
- **Historical implementation records:** `TECHNICAL_AUDIT.md` (0.9.0), `PUBLIC_DATA_BENCHMARK.md` (historical 0.9.0 benchmark plan/results), `VALIDATION_RESULTS.md` (0.10.0), and `GUI_RELEASE_AUDIT_0_11_0.md` (0.11.0). These records are retained for provenance and are not fresh acceptance evidence for 0.11.1.
- **Release notes:** `RELEASE_NOTES_DRAFT_0_11_1.md` is a draft, not a published release announcement.

The current 0.11.1 source has not yet passed Windows CI/manual acceptance, and the real experimental-data benchmark remains outstanding. Do not tag or describe this snapshot as a verified Windows or scientifically validated release until those gates are completed.

## Measurement workflow

1. Open data or use **Try example** (simulated data only).
2. Click near the centre of a bright diffraction spot.
3. Run **Measure spot profile** or confirm the real energy axis and run **Measure intensity vs energy**.
4. Review fit validity and flagged frames; save a `.leedproj` project and export CSV only after review.

## Tests

```powershell
python -m pytest -q
```

The optional Qt smoke test runs only when PySide6 and pyqtgraph are installed. The Windows Actions workflow installs the GUI dependencies and runs tests offscreen, then exercises the frozen EXE against the bundled simulated TIFF. A real interactive test on a Windows desktop is still recommended, especially for high-DPI scaling and dock dragging.

## Public experimental benchmark

The TU Wien Fe₂O₃ LEED-I(V) dataset, DOI [10.48436/hgg42-xss85](https://doi.org/10.48436/hgg42-xss85), is the intended public benchmark. The benchmark harness is in `tools/benchmark_tuwien_fe2o3.py`. No numerical agreement with real experimental outputs is claimed until the raw data and reference files are processed.

## Licence

GPL-3.0-or-later. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.

Project attribution and AI-assisted development provenance: [`CREDITS.md`](CREDITS.md).
