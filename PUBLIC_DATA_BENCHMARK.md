# Historical public-data benchmark plan — LEED Studio 0.9.0

> **Historical scope:** The harness and synthetic-fixture result described below are historical. Real experimental comparison remains outstanding for the current 0.11.1 release.

## Dataset and reference metadata

**Dataset:** ViPErLEED Supporting Information — LEED-I(V) Fe₂O₃(1-102)-(1×1)  
**Repository:** TU Wien Research Data  
**DOI:** https://doi.org/10.48436/hgg42-xss85  
**Record:** https://researchdata.tuwien.at/records/hgg42-xss85  
**Dataset licence:** CC BY 4.0 (cite the dataset creators and DOI when reusing it)

The public record lists a 2.0 GiB data archive with raw LEED-I(V) videos, a representative image, mask, pattern file, final EXPBEAMS curves, and Spot Tracker outputs including x/y coordinates, raw intensities, backgrounds, radii, significance and logs. The reference acquisition log for the `x=23.35` sequence states:

- Main input stack: `2022-06-09_03-45-22 - Ti_Fe2O3(1-102)#606 - 1x1 - x=23.35.zip`
- Dark frames: `2022-06-09_05-24-55 - Ti_Fe2O3(1-102)#606 - 1x1 - dark.zip`
- Flat field: `2022-06-09_04-34-08 - Ti_Fe2O3(1-102)#606 - 1x1 - x=23.35 - flat.zip`
- Dark-for-flat: the dark movie above
- Mask: `Spot_Tracker-mask_1x1.tif`
- Energy range: 30–750 eV, 0.5 eV steps, therefore 1,441 energy frames if both endpoints are included
- Spot indexing defined at 255.5 eV, corresponding to zero-based frame index 451
- 34 spots / 114 beams in the logged pattern fit
- Integration radius 11 px and a circular background region described in the log as 5.37 px
- Dark/flat processing string: `dark:lin flat:s50 fit4 dark2:lin`

Public sources inspected:

- Dataset record: https://researchdata.tuwien.at/records/hgg42-xss85
- Public extraction log: https://researchdata.tuwien.at/api/records/hgg42-xss85/files/LEED-IV_data_Fe2O3-1x1.zip/container/LEED-IV_data_Fe2O3-1x1/Spot_Tracker-extraction/2022-06-09_03-45-22-Ti_Fe2O3%281-102%29%23606-1x1-x%3D23.35_log.txt
- ViPErLEED package II paper: https://doi.org/10.1103/PhysRevResearch.7.013006
- ImageJ plugin documentation: https://www.viperleed.org/stable/content/imagej_plugins.html

## Validation actually completed for 0.9.0

1. Inspected the public dataset record and retrieved the public text log through the web reader. This validates the reported acquisition metadata above, not the image-processing results.
2. Added adversarial software tests reproducing the 0.8.0 false-positive Gaussian fit, frame-dependent flat normalization artifact, and neighbouring-beam switching risk.
3. Added `tools/benchmark_tuwien_fe2o3.py`, which compares LEED Studio's tracked centres with the public x/y arrays and writes per-frame errors plus a JSON report with archive SHA-256 and analysis parameters.
4. Ran that harness end-to-end against a controlled, generated multipage-TIFF fixture with known spot coordinates. The fixture produced 5/5 compared points, zero tracking failures, RMSE 0.0054 px, and all points within 1 px. This verifies the harness mechanics only; it is not a result on the TU Wien experimental data.

## What has NOT been completed

**No real raw experimental frame or published coordinate CSV has been numerically loaded and compared in this execution environment.** Attempts to download the dataset archive through the container failed because outbound DNS/network access is unavailable; the web reader also refuses the raw CSV, TIFF, and ZIP content types. Therefore no experimental RMSE, intensity correlation, peak-energy agreement, or real-data pass/fail claim is made.

This distinction is important: the benchmark harness is ready and tested on a controlled fixture, but the requested real-data validation remains blocked by data transfer into the execution environment. It would be misleading to report otherwise.

## Run the real coordinate benchmark on a machine with the dataset

1. Download `LEED-IV_data_Fe2O3-1x1.zip` from the TU Wien record and retain the original archive unchanged.
2. Extract it, then identify the `x=23.35` main video ZIP and matching `Spot_Tracker-extraction` x/y CSVs.
3. Install LEED Studio dependencies in the project environment (`pip install -e ".[dev]"`).
4. Run from the source checkout, adjusting filenames if the archive uses a slightly different encoding:

```powershell
python tools/benchmark_tuwien_fe2o3.py `
  --frames-zip "PATH\TO\2022-06-09_03-45-22 - Ti_Fe2O3(1-102)#606 - 1x1 - x=23.35.zip" `
  --reference-x "PATH\TO\2022-06-09_03-45-22-Ti_Fe2O3(1-102)#606-1x1-x=23.35_x.csv" `
  --reference-y "PATH\TO\2022-06-09_03-45-22-Ti_Fe2O3(1-102)#606-1x1-x=23.35_y.csv" `
  --beam-row 0 `
  --energy-start 30 --energy-step 0.5 --energy-end 750 `
  --start-frame 451 `
  --aperture-radius 11 --search-radius 10 `
  --background-inner 13 --background-outer 18 `
  --max-displacement 3 `
  --output results\tuwien_beam0
```

**Important:** `--beam-row 0` is an example only. Confirm which row corresponds to the intended beam and verify CSV orientation, frame ordering, and the image archive's actual frame count before trusting metrics. If a frame ZIP contains a proprietary video instead of TIFF/PNG/JPEG/BMP frames, convert it to an ordered image sequence first. The harness derives a crop envelope from the selected reference trajectory to reduce memory use; it uses only one reference coordinate to seed the tracker and does not feed the reference path into each tracking step.

The script reports median, RMSE, 95th percentile and fraction within 1 px for coordinate error. It also writes:

- `leed_studio_tracking.csv` — LEED Studio per-frame measurements with metadata sidecar
- `coordinate_errors.csv` — reference/predicted x/y and per-frame error
- `benchmark_report.json` — dataset identity, input checksum, settings, and aggregate metrics

## How to interpret the benchmark

The published coordinates were produced by ViPErLEED Spot Tracker, which uses a different processing pipeline. A nonzero discrepancy is expected and must be investigated; it is not automatically a software bug. The benchmark should be run first on several isolated, high-SNR beams, then on weak/overlapping beams and edge/mask cases.

The harness performs **coordinate comparison only**. It does not claim exact intensity equivalence because LEED Studio currently uses a circular aperture with median annular background subtraction and lacks several ViPErLEED processing stages, including fitted spatial flat-field correction, beam-tail subtraction, variable integration radii, and instrument-current normalization. Do not compare intensity values as if they had the same definition.

## Proposed acceptance criteria for a later validated release

These are proposed engineering targets, not achieved results:

- At least 95% of valid reference positions within 1 px for isolated high-SNR beams after matched frame alignment.
- Median coordinate error below 0.5 px on the selected validation subset.
- No unflagged beam identity switches in curated neighbour-crossing tests.
- Constant synthetic signal remains constant under frame-wise flat correction.
- No valid exported Gaussian fit on blank or noise-only regions in the adversarial suite.
- Intensity comparison only after implementing matching integration/background/correction definitions; report correlation, normalized RMSE, peak-energy displacement, and failed/negative intensity fractions.
- Repeat the benchmark on more than one beam and at least one independent acquisition before describing the program as experimentally validated.
