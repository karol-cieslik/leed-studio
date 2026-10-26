# LEED Studio 0.11.1 — Windows GUI guide

*For a newcomer: [README](README.md) → [current status](PROJECT_STATUS.md) → [roadmap](ROADMAP.md). This guide documents the GUI design and Windows commands; it does not imply completion of manual acceptance.*

## What changed

LEED Studio now uses a Gwyddion-inspired workspace: the image remains central while the project browser, tools/settings, I(E) curve and fit residual are dockable panels. Panels can be moved, floated, closed, shown from **View**, and their layout is restored on the next launch. Use **View → Reset workspace layout** to return to the default arrangement.

The **Project** browser lists the loaded stack, calibration inputs, selected beam, I(E) curve and spot-profile fit. Click an item to open the relevant panel. The image viewer includes a cursor readout with pixel coordinates and current working intensity. The image histogram remains a display-only contrast control; changing it does not change quantitative pixel values.

## First session

1. Choose **Try example** to explore with simulated data, or **Open data…** to load a real image/stack.
2. Click near the centre of a bright diffraction spot.
3. Choose **Measure spot profile** for a single-frame fit, or confirm the real energy start/step and choose **Measure intensity vs energy** for a stack.
4. Inspect the curve, quality flags and fit residual. Save a `.leedproj` project before exporting results.

## Workspace controls

- **View → Beginner mode** hides advanced scientific controls.
- **View → Project / Tools & settings / Intensity vs energy / Fit residual** toggles each panel.
- **View → Reset workspace layout** restores the default docking positions.
- Drag a dock title bar to reposition a panel. Drag it to the centre of another dock to tabify it. Double-click a dock title bar to float/dock it.
- **Ctrl+O** opens data; **Ctrl+S** saves the project; **F1** opens the quick-start guide; **Ctrl+0** resets image zoom; **Home/End** navigate to the first/last frame.
- Hover over the image to inspect pixel coordinates and intensity. Click the image to select a beam.

## Building a Windows executable

The repository now includes a Windows PyInstaller build and Inno Setup installer pipeline. To build locally on Windows:

1. Install Python 3.12 and Git (if building from a checkout).
2. Extract the complete source ZIP.
3. Double-click `build_windows.bat`, or run it from Command Prompt.
4. The portable app appears at `dist\LEED Studio\LEED Studio.exe`.
5. To create the installer, install Inno Setup 6 and run `iscc packaging\LEED-Studio.iss`. The installer is written to `release\LEED-Studio-Setup-0.11.1.exe`.

Alternatively, visit GitHub **Actions → Build LEED Studio for Windows → Run workflow**. The checked-in workflow triggers on **pushes to `main`** or manual dispatch; **tag pushes alone are not configured**. It installs dependencies, builds a portable PyInstaller folder and uploads the **LEED-Studio-Windows** artifact. It does **not** run tests or executable/installer acceptance checks, and does not create a GitHub Release. [A successful build artifact exists](https://github.com/karol-cieslik/leed-studio/actions/runs/38743872970), but still needs to be run and manually accepted on Windows.

**Build status (26 October 2026):** GitHub Actions successfully built and uploaded a Windows portable application on 15 October. That confirms packaging only; it does not confirm that the frozen EXE launches or works interactively. An installer recipe exists but has not been built/verified by the current workflow. See [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Scientific caution

The app remains exploratory software. A successful fit or a smooth curve does not prove the spot identity or intensity calibration is correct. Validate against experimental reference data before publication use. The included example stack is simulated, not experimental.
