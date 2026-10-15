# LEED Studio 0.11.0 — GUI and Windows packaging implementation report

Date: 2026-10-14

## Implemented

1. Replaced the tab-first visual workflow with a central image viewer and persistent `QDockWidget` panels for Project, Tools & settings, Intensity vs energy, and Fit residual.
2. Added a Project browser for image stack, calibration inputs, selected beam, curve and fit status. Clicking an entry raises the relevant panel.
3. Added image cursor coordinates and the current working pixel intensity readout.
4. Added a View menu for dock visibility, Beginner mode and Reset workspace layout.
5. Persisted main-window geometry and dock state through `QSettings`.
6. Added native Qt toolbar icons and direct actions to raise the curve and tools panels.
7. Added a custom application icon to the source package and wheel.
8. Added `LEED_Studio.spec` for a PyInstaller onedir Windows build, `build_windows.bat`, an Inno Setup installer recipe, and GitHub Actions workflow that runs tests, builds the executable and installer, then uploads artifacts.
9. Expanded the optional Qt smoke test to assert the central image workspace, project browser, dock widgets and beginner-mode defaults.
10. Added release-configuration regression tests and refreshed the Windows GUI guide and README.

## Verification performed in this environment

- `python -m compileall -q leed_studio tests tools`: passed.
- `python -m pytest -q`: **46 passed, 1 skipped**.
- Wheel built with local build dependencies using `pip wheel --no-deps --no-build-isolation`.
- Wheel installed into an isolated target directory; `import leed_studio` succeeded, version was `0.11.0`, and the ICO asset was present.
- Source ZIP integrity checked after packaging.

## Not verified here

- PySide6 and pyqtgraph are not installed in this environment. Installing them failed because package-index network access is unavailable. Consequently, the optional GUI smoke test is skipped here, and the application has not been launched interactively in this run.
- No Windows executable or installer has been built here. PyInstaller is not available, and a Windows executable must be built on a Windows runner. The included GitHub Actions workflow is the implementation path to produce the actual `.exe` and portable ZIP.
- Dock drag/drop behavior, high-DPI scaling, Windows file dialogs, display scaling, and Qt plugin bundling require the Windows workflow and a real Windows acceptance test.

## Known limitations

- The data browser is a navigator, not a full arbitrary multi-dataset document model.
- Undo/redo for scientific operations, worker-thread processing, progress/cancellation, a multi-beam table, and autosave/recovery are not implemented in this pass.
- This does not change the scientific validation status: LEED Studio remains exploratory and not numerically benchmark-validated against the real TU Wien Fe2O3 reference outputs.

## Windows build instructions

Local build: run `build_windows.bat` from the project root on a Windows machine with Python 3.12. The portable executable will be `dist\LEED Studio\LEED Studio.exe`. To build the installer, install Inno Setup 6 and run `iscc packaging\LEED-Studio.iss`; output is `release\LEED-Studio-Setup-0.11.0.exe`.

CI build: push the project to GitHub, then run **Actions → Windows application build → Run workflow**, or push a tag matching `v*`. The workflow runs Qt smoke tests on a Windows runner, packages the app, attempts a startup smoke test, builds the installer, and uploads artifacts.
