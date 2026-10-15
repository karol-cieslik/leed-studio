# Windows executable acceptance test plan — LEED Studio 0.11.1

This document distinguishes automated packaging tests from scientific validation and manual desktop acceptance.

## Automated checks in `.github/workflows/windows-build.yml`

The Windows runner is intended to perform these checks in order:

1. Compile application, test, and benchmark Python files.
2. Run unit, project-I/O, packaging and offscreen Qt tests.
3. Run the source application's `--self-test-gui` path.
4. Build the portable one-folder application using `LEED_Studio.spec`.
5. Run `LEED Studio.exe --self-test-gui` with the bundled runtime and data.
6. Launch the ordinary executable for an eight-second startup check.
7. Compile the Inno Setup installer.
8. Install silently into a temporary per-user directory.
9. Run the installed executable's `--self-test-gui` path.
10. Uninstall and upload the installer, portable ZIP and a test record.

The self-test exercises Qt application construction, bundled sample TIFF discovery/loading, a Gaussian spot-profile fit, I(E) tracking, and creation of per-frame results. It exits non-zero on failure.

## What this does and does not prove

A passing workflow provides evidence that the packaged app starts in the CI environment, includes required runtime libraries and the sample data, and completes a controlled synthetic workflow. It does **not** prove scientific agreement with experimental LEED data, compatibility with every detector's TIFF metadata, or usability on every Windows graphics driver.

The ordinary startup test confirms the process survives startup; the self-test is the stronger automated check. Neither replaces a human test on a normal desktop because CI uses the Qt offscreen platform.

## Manual acceptance checklist on a Windows 10/11 desktop

- [ ] Install using the installer without administrator permissions.
- [ ] Launch from the Start menu and confirm the main window and icon appear.
- [ ] Try the example; select the spot and complete fit and I(E) measurement.
- [ ] Open a known multipage TIFF from a path containing spaces and non-ASCII characters.
- [ ] Test Open/Save dialogs, project save, close, relaunch, and project reopen.
- [ ] Export fit CSV and I(E) CSV; verify expected files and provenance sidecar.
- [ ] Move, float, tab, close and restore dock panels.
- [ ] Reset the workspace layout and restart; confirm layout behavior is sensible.
- [ ] Test 100%, 125%, 150% and 200% Windows display scaling.
- [ ] Test a large stack and note peak memory, responsiveness and cancellation behavior.
- [ ] Test masked regions, detector edges, weak spots and neighbouring spots.
- [ ] Uninstall and confirm the application files are removed while user projects are preserved.

Record Windows version, display scale, monitor configuration, stack dimensions, result, and screenshots for any failure.

## Current execution status

Local environment checks have run, but this environment is not Windows and does not have PySide6 or pyqtgraph installed. Therefore, the Windows workflow, actual `.exe`, installer, and manual desktop checklist are **not yet executed**. Do not represent the release as Windows-verified until a run of the workflow succeeds.
