# Changelog

## 0.11.1 — Windows executable acceptance checks and full user documentation

- Added a non-interactive `--self-test-gui` entrypoint that opens the Qt application, loads the bundled simulated TIFF, performs a spot-profile fit and an I(E) workflow, and checks the resulting data.
- Expanded the Windows CI workflow to run compilation, unit/Qt tests, the frozen EXE self-test, normal GUI startup, installer build, installation, installed-EXE self-test and uninstallation.
- Changed the installer default to a per-user installation under Local AppData, avoiding an unnecessary administrator prompt.
- Added a comprehensive software overview and user manual covering purpose, scientific basis, Gwyddion UX inspiration, ViPErLEED as a comparison reference, installation, workflow, energy-axis confirmation, calibration, exports, limitations and licensing.
- Expanded packaging regression tests for the self-test path, installer workflow, sample data and documentation.
- The Windows CI workflow has not been run from this environment; actual EXE/installer outputs remain unverified until that Windows job executes.

## 0.11.0 — Gwyddion-inspired Windows workspace

- Replaced the image/curve/residual tab workflow with a central image viewer and dockable project, tools, I(E) and fit-residual panels.
- Added a project data browser with entries for stack, calibration, selected beam and analysis outputs.
- Added image cursor readout for pixel coordinates and working intensity.
- Added View menu controls for dock visibility, Beginner mode and resetting the workspace layout.
- Persisted window geometry and dock layout with QSettings.
- Added native-style toolbar icons and quick access to curve/tools panels.
- Added PyInstaller onedir spec, Windows build batch file, Inno Setup recipe and GitHub Actions workflow for Windows test/build/artifact upload.
- Added release configuration regression tests.
- Actual Windows binary and interactive GUI runtime are not verified in the current Linux environment.

## 0.10.0 — Windows GUI usability pass

- Reorganised the GUI around common beginner tasks and reduced toolbar clutter.
- Added simulated example-stack access and a four-step workflow banner.
- Hid detailed tracking parameters and calibration tools behind an opt-in advanced-settings checkbox.
- Added a Quick start guide (Help → Quick start guide / F1), plain-language button labels, and context tooltips.
- Added a scrollable controls panel and a smaller minimum window size.
- Made energy-axis status explicit and reset the initial energy start to an untrusted placeholder of 0 eV.
- Moved calibration actions into the advanced panel and disabled correction application until calibration inputs are loaded.
- No claim of an interactive Windows GUI test: Qt dependencies were not installed in the previous build environment.
