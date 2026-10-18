# LEED Studio 0.11.1 — Windows GUI guide

## What changed

LEED Studio now uses a Gwyddion-inspired workspace: the image remains central while the project browser, tools/settings, I(E) curve and fit residual are dockable panels. Panels can be moved, floated, closed, shown from **View**, and their layout is restored on the next launch. Use **View → Reset workspace layout** to return to the default arrangement.

The **Project** browser lists the loaded stack, calibration inputs, selected beam, I(E) curve and spot-profile fit. Click an item to open the relevant panel. The image viewer includes a cursor readout with pixel coordinates and current working intensity. The image histogram remains a display-only contrast control; changing it does not change quantitative pixel values.

## First session

The first time you open the app, a small simulated practice stack loads automatically. Click near the centre of a bright spot, then choose **Measure spot profile** or **Measure intensity vs energy**. The practice stack uses a known demo axis (80 eV start, 5 eV per frame) so you can try the full measurement flow without your own files.

Review the curve, fit residual and any quality flags. Try **Save project…** and the CSV export buttons. The walkthrough is in [BEGINNER_WALKTHROUGH.md](BEGINNER_WALKTHROUGH.md). The example is synthetic, not an experimental result. Later, use **File → Try example data** to load it again, or **Open data…** for your own image/stack.

For real data, enter the first-frame energy and step from your experiment records before confirming the axis. Do not use the demo values for your experiment.

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

Alternatively, push the project to GitHub and run **Actions → Windows application build → Run workflow**. Tag pushes such as `v0.11.1` also trigger a build. The workflow runs tests on Windows, builds the app, attempts executable and installer acceptance checks, and uploads portable ZIP and installer artifacts to the workflow run. It does not automatically publish a GitHub Release.

**Build status:** this source bundle contains the build configuration, but the actual Windows binary has not been generated in this Linux environment. Qt/PyInstaller installation required network access, which was unavailable here. The GitHub Actions workflow must run on a Windows runner to produce and validate the real `.exe`.

## Scientific caution

The app remains exploratory software. A successful fit or a smooth curve does not prove the spot identity or intensity calibration is correct. Validate against experimental reference data before publication use. The included example stack is simulated, not experimental.
