# LEED Studio — software overview and user manual

**Version:** 0.11.1  
**Status:** Exploratory scientific software / pre-release  
**Platform:** Windows 10/11 (intended), Python source also supports other platforms where Qt dependencies work  
**License:** GNU General Public License v3 or later (GPL-3.0-or-later)

> **Current GitHub verification (26 October 2026):** A Windows **portable executable was built and uploaded** in [Actions run 38743872970](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970), but that job did **not** run application tests, launch the frozen executable, or make an installer. Earlier sections of this manual describe what source/build scripts are designed to support; they are not certification of the current binary. For exact status, see [PROJECT_STATUS.md](PROJECT_STATUS.md); for next steps, see [ROADMAP.md](ROADMAP.md).

## 1. What LEED Studio is

LEED Studio is a desktop application for exploring low-energy electron diffraction (LEED) images and image stacks. It is designed to help a researcher load images, inspect diffraction spots, estimate a spot profile, follow a selected spot across frames, plot an intensity-versus-energy curve (I(E)), inspect questionable measurements, and export the data and settings used.

The long-term goal is a friendly, standalone LEED analysis workspace: the user should be able to see the image, project contents, tools, curve, and fit diagnostics together rather than manage a collection of scripts. The interface is inspired by established scientific image-analysis applications, especially the dockable, image-centred interaction model associated with Gwyddion.

**Scientific caution:** LEED Studio 0.11.1 is an exploratory prototype. Its basic tracking and intensity methods have not been demonstrated to reproduce ViPErLEED Spot Tracker outputs on the public Fe₂O₃ experimental benchmark. Do not use its results as publication-grade measurements without independent verification.

## 2. What it is based on and what inspired it

### 2.1 Scientific problem

LEED experiments produce diffraction patterns whose spot positions and intensities can vary with electron energy and experimental conditions. Extracting a useful I(E) curve requires more than plotting pixel values: the spot needs to be located consistently, a background estimated, intensity measured using a defined region, and each measurement associated with the correct energy and processing settings.

LEED Studio aims to make these steps inspectable and repeatable for experimental image stacks.

### 2.2 Gwyddion: interaction inspiration, not a code dependency

[Gwyddion](https://gwyddion.net/) is a free scientific data-visualization and analysis application used extensively for scanning probe microscopy. LEED Studio borrows ideas from its desktop interaction model:

- a central image/data view;
- persistent, dockable tool and data panels;
- direct interaction with the displayed data;
- analysis tools that can remain visible beside the image;
- a configurable workspace rather than a sequence of disconnected wizard pages.

LEED Studio is **not an official Gwyddion project, plugin, fork, or endorsed product**. Its GUI is implemented with PySide6 (Qt) and pyqtgraph. The inspiration is the user-experience model; this project does not claim to reuse Gwyddion source code.

### 2.3 ViPErLEED: scientific reference and benchmark

[ViPErLEED](https://github.com/viperleed/viperleed) and its [ImageJ plugin](https://github.com/viperleed/viperleed-imagej) are important public references for LEED experiment analysis. The ImageJ Spot Tracker workflow provides a reference for beam tracking, spot-intensity extraction, background handling, and I(E) curves.

LEED Studio uses these tools as **scientific references for comparison and validation**, not as proof that its current algorithms are equivalent. No claim of numerical equivalence is made. Any future code adaptation from GPL-licensed ViPErLEED components must retain required notices and comply with the relevant licence terms.

The intended public experimental benchmark is the TU Wien Fe₂O₃ LEED-I(V) dataset:

- Dataset record: https://researchdata.tuwien.at/records/hgg42-xss85
- DOI: https://doi.org/10.48436/hgg42-xss85

That record documents raw image/video data and published Spot Tracker outputs. A complete numerical comparison against the experimental reference outputs remains outstanding.

### 2.4 Technical stack

| Component | Role |
|---|---|
| Python | Application and analysis logic |
| PySide6 / Qt | Native desktop widgets, menus, dialogs, dock panels |
| pyqtgraph | Interactive image and curve views |
| NumPy | Numerical arrays and data operations |
| SciPy | Gaussian fitting and numerical methods |
| Pillow / tifffile | Common image and TIFF-stack input |
| pytest | Automated tests |
| PyInstaller | Bundles the Python application into a Windows application folder |
| Inno Setup | Builds the optional Windows installer |

The application is intended to run locally. Its normal analysis workflow does not require a cloud account.

## 3. What it aims to solve

The project aims to reduce friction in a typical LEED image-analysis workflow:

1. **Inspect a stack:** navigate frames and adjust display contrast without altering measurement values.
2. **Select a spot:** click the approximate centre of a diffraction spot.
3. **Measure a profile:** fit an elliptical Gaussian to a local region and inspect residuals and validity diagnostics.
4. **Measure I(E):** track the selected spot through the stack and estimate a background-corrected intensity for each frame.
5. **Review problems:** inspect per-frame quality flags and move to flagged frames.
6. **Preserve work:** save a `.leedproj` project containing image arrays, settings and available results.
7. **Export results:** write CSV output and provenance/settings information for downstream analysis.

The longer-term direction includes multi-beam analysis, crystallographic beam indexing, stronger motion prediction, calibrated uncertainties, robust large-stack processing, and validated compatibility with published LEED analysis workflows. Those goals are not all implemented in this release.

## 4. Installation and launch on Windows

### Option A — portable Windows build

When a Windows release artifact is available, extract the `LEED-Studio-Portable-0.11.1.zip` folder to a location where you have write/read access and double-click **LEED Studio.exe** inside it. Keep the files together: the executable relies on adjacent bundled libraries and resources.

### Option B — Windows installer

Run `LEED-Studio-Setup-0.11.1.exe`, follow the installer, and launch LEED Studio from the Start menu. The installer is designed for a per-user installation and does not need administrator privileges by default.

**Release availability note:** GitHub Actions successfully produced a portable Windows artifact on 15 October 2026, but did **not** test its startup or GUI. Download the `LEED-Studio-Windows` artifact from [the latest run](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) and extract its `dist` folder; keep the `LEED Studio` folder and adjacent `_internal` content together. There is **no verified public installer or published GitHub Release** as of this audit. A source ZIP is not itself a Windows executable.

### Option C — run from source

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/ and ensure the Python launcher (`py`) is installed.
2. Extract the source ZIP.
3. Open PowerShell in the extracted project directory.
4. Run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install_windows.ps1
   ```

5. To launch again later, run `run_windows.bat` if included in your source bundle, or:

   ```powershell
   .\.venv\Scripts\python.exe -m leed_studio
   ```

If Windows SmartScreen warns about an unsigned installer, verify that the file came from the project's trusted release location. This project does not currently claim a code-signing certificate.

## 5. First session: four steps

### Step 1 — open data or practise

- Click **Try example** to open a small simulated LEED-like stack packaged with the application.
- Or click **Open data…** and select a supported image or TIFF stack.

The example is synthetic practice data, not an experimental dataset. Do not cite its measurements as physical results.

Supported input formats currently include common TIFF (`.tif`, `.tiff`), PNG, JPEG and BMP images. Multipage TIFF is the primary stack format. TIFFs with unusual axis order, multiple channels, or detector-specific metadata may need conversion to a documented grayscale stack before use. Always confirm the displayed frame count and orientation.

### Step 2 — inspect the image

- Use the frame slider to navigate the stack.
- Use the image viewer's zoom/pan controls to inspect a spot.
- Adjust the histogram/contrast display to make weak spots easier to see. Display contrast changes are for viewing and do not change the quantitative pixel values.
- Move the cursor over the image to inspect pixel coordinates and working intensity.
- Click near the centre of a bright diffraction spot to select it.

The coloured overlays show the selected spot, measurement aperture, background annulus and tracking search region where applicable. Check that these regions do not unintentionally overlap a neighbouring beam, detector edge, dead area or masked region.

### Step 3 — choose the measurement

**Measure spot profile**

This fits an elliptical Gaussian to a local image region around the selected point. Review the fitted centre, amplitude, widths, fit residual image, optimizer status and validity flags. An optimizer can converge mathematically without a scientifically meaningful spot, so a successful numerical fit is not by itself proof that the model is appropriate.

**Measure intensity vs energy**

This tracks the selected spot across all frames and estimates an intensity after background subtraction. It produces a curve and per-frame table. Review every flagged frame and any large position jump or missing/invalid intensity before export.

### Step 4 — review and save

- Click points on the I(E) curve or rows in the measurement table to inspect the associated frame.
- Use **Previous flagged frame** / **Next flagged frame** to review quality warnings.
- Save the work as a `.leedproj` project before leaving the session.
- Export the fit or I(E) CSV only after checking the measurement and its settings.

## 6. Energy-axis calibration: important

LEED Studio cannot infer the physical electron energy from an arbitrary TIFF stack unless that information is available and correctly interpreted by a supported metadata reader. In this version, the I(E) energy axis is entered manually.

Before measuring I(E):

1. Find the actual energy corresponding to frame 1 in your acquisition metadata.
2. Enter that value as **Energy start (eV)**.
3. Enter the real step between consecutive frames as **Energy step (eV)**.
4. Check whether the sequence is ascending, descending, contains missing frames, or uses non-uniform energy steps. This version assumes a constant step and does not represent arbitrary per-frame energy values.
5. Tick the confirmation box only after checking the acquisition record.

A wrong energy axis can produce a visually smooth but physically mislabelled curve. Keep a copy of the original acquisition log with the project.

## 7. Calibration, corrections, and masks

Dark frames, flat-field frames, dark-for-flat frames and masks must correspond to the detector, acquisition settings and stack being analysed.

- Inspect calibration data before applying corrections.
- Confirm whether a calibration represents one static reference or synchronized per-frame data.
- Check that image dimensions, frame counts and axes are compatible.
- Verify mask polarity: determine which pixels are excluded and which are valid.
- Check the corrected image for NaNs, saturated pixels, dead pixels, gradients and artificial intensity structure.
- Keep the original raw data unchanged and save a project before trying a different correction setup.

Flat-field conventions differ across detectors and experimental pipelines. LEED Studio's current correction methods are not demonstrated to reproduce every ViPErLEED calibration option. If a correction changes a known uniform signal unexpectedly, stop and investigate before measuring experimental curves.

## 8. Understanding results and warnings

The application can report fitted centre, amplitude, background, widths, residuals, SNR-like diagnostics, intensity estimates, per-frame displacement and quality flags.

These values have different meanings:

- **Fit convergence:** the numerical optimizer reached a solution; it does not prove the physical model is suitable.
- **Fit validity:** application-specific rejection checks passed; this is not a guarantee of physical correctness.
- **SNR / quality flags:** heuristic diagnostics that help identify questionable frames; they are not calibrated probabilities.
- **Centre standard errors:** model-based estimates; not experimentally validated uncertainty intervals.
- **Background-corrected intensity:** the output of the current aperture and annulus procedure; it may differ from intensity definitions used by other packages.

If a spot is weak, overlaps another spot, moves substantially, approaches the image boundary, or is obscured by a mask, treat its curve as uncertain. Do not silently interpolate failed measurements for publication without documenting and validating the method.

## 9. Projects, exports, and reproducibility

### Project files

A `.leedproj` project is a portable archive intended to retain the image data, correction arrays when available, selected point, settings and saved results. Save a project at meaningful checkpoints. Keep a separate copy of the raw experimental files.

### CSV and provenance

CSV files are convenient for plotting or analysis in Python, Origin, Excel, or similar tools. Where generated, the accompanying JSON provenance sidecar records settings and software information. Preserve the CSV and sidecar together.

For reproducible work, also record:

- the original data filename and checksum;
- detector/acquisition metadata and energy mapping;
- dark/flat/mask filenames and how they were applied;
- software version;
- aperture, background and tracking settings;
- all warnings and any manual exclusions;
- the reference workflow used for cross-checking.

## 10. Workspace and interaction model

The desktop layout is inspired by Gwyddion's dockable scientific workspace. Typical panels include:

- **Project/data browser:** navigate the loaded stack and available results.
- **Image viewer:** inspect frames, select spots, and view measurement overlays.
- **Tools/settings:** choose fit and tracking parameters.
- **Intensity vs energy:** inspect the curve and frame table.
- **Fit residual:** inspect differences between the fitted model and observed image.

Panels can be shown, hidden, moved or tabbed according to Qt's dock-widget behavior. The View menu includes layout-related actions. If the workspace becomes confusing, use the reset-workspace action to return to the default arrangement.

The beginner-oriented controls are intended to keep common actions obvious while preserving advanced controls for users who need them.

## 11. Known limitations

This is a pre-release research prototype. Important limitations include:

- no completed numerical benchmark against the public TU Wien Fe₂O₃ Spot Tracker outputs;
- baseline tracking rather than a demonstrated equivalent of ViPErLEED Spot Tracker;
- limited handling of overlapping spots, long low-signal gaps and spot identity ambiguity;
- intensity estimates depend on the current aperture and annular-background model;
- no full crystallographic beam indexing or symmetry-equivalent beam analysis;
- constant-step energy-axis assumption;
- no validated detector-specific metadata import for all acquisition systems;
- large image stacks can consume substantial memory, and long analysis may not yet provide full worker-thread progress/cancellation;
- automated GUI tests do not replace manual acceptance tests on real Windows desktops and high-DPI displays;
- the Windows executable/installer is only a release artifact after the Windows build pipeline succeeds.

Use a trusted established package and independent analysis for publication-critical results until the relevant benchmark comparisons are complete.

## 12. Building and testing the Windows executable

Build on Windows, preferably Windows 11 with Python 3.12:

1. Extract the full source repository.
2. Open PowerShell or Command Prompt in the project root.
3. Run `build_windows.bat`.
4. The script installs dependencies, compiles Python files, runs tests, executes a Qt offscreen workflow test, builds with PyInstaller, and runs the frozen application's `--self-test-gui` mode.
5. For the installer, install Inno Setup 6 and run:

   ```powershell
   iscc packaging\LEED-Studio.iss
   ```

6. Test the portable executable on a clean Windows user profile and a second machine if possible.
7. Test the installer, Start-menu launch, uninstall, file dialogs, project save/open, CSV export, high-DPI scaling and a real image stack.

The **current checked-in** GitHub Actions workflow `.github/workflows/windows-build.yml` only checks out source, configures Python 3.11 on Windows, installs dependencies, runs `pip check`, builds with PyInstaller and uploads the `LEED-Studio-Windows` folder artifact. [The latest run](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970) succeeded. Unlike `build_windows.bat` and earlier documented workflow plans, it does **not** run unit/Qt tests, self-test the frozen executable, build an installer, or test install/uninstall. These are future release-acceptance tasks, not passed steps. Also note that at least two assertions in `tests/test_release_packaging.py` still expect the former more extensive CI and must be reconciled before the present `main` suite can be considered green.

The `--self-test-gui` command is implemented in source to check that a Qt window opens, the bundled synthetic TIFF loads, a spot fits, and an I(E) table is produced. **Its presence does not show that it was run on the GitHub-built artifact.** When run successfully, this is a packaging smoke test on simulated data, not a scientific validation.

## 13. Research references and acknowledgements

- Gwyddion project: https://gwyddion.net/
- ViPErLEED source repository: https://github.com/viperleed/viperleed
- ViPErLEED ImageJ plugin: https://github.com/viperleed/viperleed-imagej
- TU Wien Fe₂O₃ LEED-I(V) public data: https://doi.org/10.48436/hgg42-xss85
- Python: https://www.python.org/
- Qt for Python / PySide6: https://doc.qt.io/qtforpython-6/
- pyqtgraph: https://www.pyqtgraph.org/
- NumPy: https://numpy.org/
- SciPy: https://scipy.org/
- Pillow: https://python-pillow.org/
- tifffile: https://github.com/cgohlke/tifffile
- PyInstaller: https://pyinstaller.org/
- Inno Setup: https://jrsoftware.org/isinfo.php

Gwyddion is acknowledged as a user-experience inspiration. ViPErLEED and its ImageJ plugin are acknowledged as scientific reference implementations for comparison and validation. These acknowledgements do not imply affiliation or endorsement.

## 14. License, contributions, and project attribution

LEED Studio is distributed under GPL-3.0-or-later; see `LICENSE` and `THIRD_PARTY_NOTICES.md`. Third-party libraries retain their own licenses. Any reuse or adaptation of code from external GPL projects must be reviewed for licence compatibility and accompanied by the required notices/source availability.

Project direction and AI-assisted development provenance are documented in [`CREDITS.md`](CREDITS.md). Review that statement before public release and adjust it to match the actual division of work and any applicable employer, funder, journal, or repository policy.

Contributions should include a description of the scientific behavior changed, regression tests, and any effect on exported data or reproducibility.
