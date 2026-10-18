# LEED Studio

LEED Studio helps you explore low-energy electron diffraction (LEED) images and image stacks. You can inspect frames, select a diffraction spot, fit its profile, follow its intensity across an energy series, review warnings, save a project, and export results.

> **Scientific status:** LEED Studio is exploratory research software. Its measurements have not been validated as a replacement for ViPErLEED Spot Tracker. Check results independently before relying on them for research conclusions or publication.

## Start here

1. Open LEED Studio. The first time, it loads a small **simulated practice stack** automatically.
2. Click near the centre of a bright spot in the image.
3. Click **Measure spot profile** to fit one frame, or **Measure intensity vs energy** to follow the spot through the stack.
4. Review the fit, curve, and any flagged frames. Try **Save project…** and the CSV export buttons to practise saving your work.

The practice stack is synthetic. It is included to learn the controls and check that the app runs; it is not experimental data. Choose **File → Try example data** to load it again later. Press **F1** for the quick guide.

## Use your own data

Open a grayscale image or multipage TIFF stack with **Open data…**. PNG, JPEG, BMP, and TIFF images are supported; multipage TIFF is the main stack format. Before measuring an I(E) curve, enter the actual first-frame energy and energy step from your experiment records, then confirm the energy axis. The app cannot infer those values from every file format.

Keep the original files unchanged. Check spot selection, corrections, fit diagnostics, and quality flags before exporting. A detailed explanation is in the [software overview and user manual](SOFTWARE_OVERVIEW_AND_USER_MANUAL.md).

## Windows download and build

When a Windows Actions run finishes successfully, open the run and download its **LEED-Studio-Windows** artifact. Extract the downloaded ZIP and keep the extracted folder together; launch **LEED Studio.exe** from that folder. The app needs the adjacent `_internal` files.

To build from source on Windows, see [WINDOWS_GUI_GUIDE.md](WINDOWS_GUI_GUIDE.md). The GitHub Actions workflow builds a portable folder artifact; an Actions artifact is not the same as a published GitHub Release or installer.

## Guides

- [Beginner walkthrough](BEGINNER_WALKTHROUGH.md) — practise the main workflow with the included stack.
- [Full software overview and user manual](SOFTWARE_OVERVIEW_AND_USER_MANUAL.md) — formats, energy axis, calibration, results, limitations, and reproducibility.
- [Windows GUI guide](WINDOWS_GUI_GUIDE.md) — panels, shortcuts, and Windows build steps.
- [Current validation and release status](VALIDATION_RESULTS_0_11_1.md) — what has and has not been checked.

## Public research benchmark

The intended experimental comparison uses the TU Wien [Fe₂O₃ LEED-I(V) dataset](https://doi.org/10.48436/hgg42-xss85). It is separate from the small simulated practice stack included in this app. Numerical agreement with the published reference outputs has not yet been established.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
