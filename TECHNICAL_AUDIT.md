# Historical technical audit — LEED Studio 0.9.0 (not current-release validation)

Date: 2026-10-14

## Executive summary

> **Historical scope:** This audit records checks performed for version 0.9.0. It is not evidence that the same findings were re-tested in version 0.11.1.

Version 0.9.0 fixes several high-risk issues reproduced in version 0.8.0: a constant image could be accepted as a successful Gaussian fit; frame-wise flat-field values could introduce an artificial energy trend; and a bright neighbouring beam could steal the tracker while later frames appeared healthy. The release also adds an explicit energy-axis confirmation, explicit calibration-stack interpretation, stronger project validation, and a tested public-dataset benchmark harness.

**Scientific release status remains NOT VALIDATED.** The public TU Wien Fe₂O₃ dataset record and its text extraction log were inspected, but the binary raw video and CSV coordinate arrays could not be retrieved into this execution environment. The benchmark runner was executed against a controlled synthetic fixture, not against the real experiment. No real-data RMSE or intensity-agreement number is claimed.

## Confirmed 0.8.0 failure reproductions and 0.9.0 outcomes

### 1. False-positive fit on constant image

Fixture: 41×41 pixels, every pixel exactly 100.

- 0.8.0: `fit.success == True`, despite no diffraction spot and undefined R².
- 0.9.0: `optimizer_success == True` but `success == False`, `valid == False`, with flags for undefined R², insignificant amplitude, and fit amplitude below three times robust border noise.

Implementation: `leed_studio/analysis.py::fit_spot`. Fit export is disabled for scientifically invalid fits.

### 2. Artificial energy trend from frame-wise flat normalization

Fixture: two raw frames with constant value 100; flat frames are uniformly 10 and 20.

- 0.8.0: corrected means were `[150, 75]` because one global normalization factor was applied across both calibration frames.
- 0.9.0: frame-wise mode returns `[100, 100]`; default average mode also returns `[100, 100]` for this static-signal fixture.

Implementation: `correct_image_stack`. Each flat calibration frame receives its own median normalization. `calibration_mode="average"` is the safe default; `calibration_mode="framewise"` is explicit and validates frame count. This still is not the ViPErLEED polynomial flat-field correction.

### 3. Silent switch to a brighter neighbouring beam

Fixture: a spot moves x=20→21→22 while a brighter distractor remains near x=27.

- 0.8.0: tracker followed the distractor, producing x `[20.0, 27.0, 27.0]`; the first jump was flagged but the next frame was `ok`.
- 0.9.0: tracker followed the intended spot, producing x `[20.0, 21.01, 22.21]` with no failures in this fixture.

Implementation: `track_spot_series` selects the nearest significant local maximum after the seed, narrows centroid windows when competing maxima are nearby, and rejects implausible movement using `max_displacement_px`. This is safer but not a full data-association/Kalman solution; unresolved overlap can still cause flagged failures or identity uncertainty.

## Additional changes

- Uniform/no-signal frames now produce explicit failed rows and NaN intensity rather than apparently valid zero-intensity measurements.
- Fit checks now include robust border-noise SNR and width-bound detection; these are conservative heuristics, not a complete noise model.
- The energy start/step must be explicitly confirmed before I(E) extraction; changing either invalidates the confirmation.
- Calibration mode and maximum per-frame displacement are configurable and included in project/export metadata.
- Loading calibration inputs or changing their interpretation clears existing results to prevent stale exports.
- Export metadata distinguishes applied corrections from pending calibration inputs.
- 0.8.x saved fits are not silently treated as scientifically validated after loading.
- Project ZIPs reject duplicate/unexpected top-level members, unsupported array types, invalid shapes, non-dictionary metadata, non-finite raw/calibration/mask values, and infinite working-stack values.
- Added `tools/benchmark_tuwien_fe2o3.py` to compare a selected tracked beam against the published x/y arrays, crop image frames to the reference trajectory envelope to reduce memory, and write per-frame errors, aggregate metrics, and provenance.

## Test results

- 43 automated tests passed.
- One optional Qt smoke test skipped because PySide6 and pyqtgraph are unavailable in this environment.
- Python syntax compilation passed.
- Benchmark harness ran end-to-end on a controlled 5-frame TIFF fixture: 5/5 compared points, zero failed frames, RMSE 0.0054 px, 100% within 1 px. This validates the harness path, not the experimental dataset.
- Windows GUI launch/install was not tested.

## Real public dataset inspected

TU Wien record: https://researchdata.tuwien.at/records/hgg42-xss85 (DOI 10.48436/hgg42-xss85). The record lists a 2.0 GiB data archive and published Spot Tracker outputs. Its public text log for the x=23.35 acquisition documents 30–750 eV, 0.5 eV steps, spot indexing at 255.5 eV, 34 spots/114 beams, an 11 px integration radius, and processing setting `dark:lin flat:s50 fit4 dark2:lin`.

The log was retrieved as text. Attempts to retrieve the raw ZIP/TIFF/CSV binary files failed: outbound DNS/network access was unavailable to the execution container and the web reader rejects the binary/CSV MIME types. Therefore, raw image tracking and comparison to the actual published x/y arrays could not be run here. See `PUBLIC_DATA_BENCHMARK.md` for the reproducible command and limitations.

## Remaining high-priority issues

1. **Complete real-data coordinate benchmark.** Run the harness on multiple beams and confirm frame order, CSV orientation, and reference beam row. This is still a release blocker.
2. **Intensity equivalence.** The current hard-edged circular aperture and median-annulus background do not reproduce ViPErLEED's integration, background, flat-field and beam-tail handling. Do not compare intensities as equivalent until these methods are matched.
3. **Spot data association.** Nearest-peak plus motion gating is a safer baseline but does not solve crossings, overlapping beams, or long low-SNR gaps. Implement candidate tracking with explicit ambiguity states and predicted motion before claiming robustness.
4. **Calibration fidelity.** Implement and validate the published polynomial flat-field correction and its dark-frame semantics; document how time/energy-dependent darks and flats should be synchronized.
5. **Large-stack architecture.** Loading, correction and analysis still retain the whole stack in memory. Add lazy frame readers, ROI streaming, background workers, progress and cancellation.
6. **Energy metadata.** Confirmation prevents accidental unreviewed defaults but does not parse detector metadata or instrument energy calibration files. Add importable energy vectors and nonuniform energy support.
7. **GUI/runtime.** Run the GUI smoke test on a Qt-enabled system and on Windows, including DPI scaling, file dialogs, curve click-to-frame, project round-trip, masks, and correction error paths.
8. **Project semantics.** Add schema migrations for future versions, stricter semantic validation of all measurement rows, and regression tests for interrupted/low-disk saves.
9. **Uncertainty.** Fit errors assume independent homoscedastic residuals and tracker SNR is heuristic. Implement a noise model and validate uncertainty coverage on replicate measurements.
10. **Multi-beam workflow.** Add a persistent beam list, batch measurement, beam indexing/pattern fitting, equivalent-beam averaging and diagnostic plots.

## Scientific position

LEED Studio 0.9.0 is a safer exploratory prototype. It is not an experimentally validated replacement for ViPErLEED Spot Tracker and should not yet be described as such. The next milestone is the real Fe₂O₃ coordinate benchmark, followed by matched intensity-processing definitions and an actual Windows GUI smoke test.
