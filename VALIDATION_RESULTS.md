# Historical validation results — LEED Studio 0.10.0

> **Historical scope:** Results below refer to version 0.10.0 and must not be interpreted as fresh test results for 0.11.1.

Date: 2026-10-14

## Code and package checks

- Python syntax compilation: passed (`python -m py_compile leed_studio/*.py`).
- Automated test suite: **43 passed, 1 skipped**.
- Wheel build: passed using installed build tools and `--no-build-isolation`.
- Wheel inspection: confirmed the GUI module and packaged simulated example TIFF are present.
- Source package includes the Windows PowerShell installer, launcher, quick-start documentation, tests and benchmark harness.

## GUI test boundary

The optional offscreen Qt smoke test is skipped because PySide6 and pyqtgraph are unavailable in this environment. Therefore, no interactive GUI launch was performed here. Windows 10/11 runtime behavior, high-DPI scaling, dialog behavior, keyboard navigation, and installer behavior still need actual Windows acceptance testing.

## Scientific validation boundary

The suite covers controlled synthetic fixtures. The public TU Wien Fe₂O₃ dataset has not yet been processed through LEED Studio for a numerical comparison. No experimental coordinate RMSE or intensity-curve agreement is claimed. The tracker remains a baseline implementation and is not equivalent to ViPErLEED Spot Tracker.

## GUI changes in 0.10.0

- Beginner-first toolbar and workflow banner.
- Packaged simulated example stack.
- Hidden advanced controls by default.
- Quick-start guide (F1), contextual tooltips, simpler button names.
- Scrollable controls, reduced minimum window size, clearer energy-axis state.

## Next release gates

1. Launch and test the GUI on Windows 10/11 at 100%, 125%, 150% and 200% display scaling.
2. Verify open/example/project/save/discard/cancel, spot selection, fit, curve measurement, flagged-frame navigation and exports.
3. Add worker threads with progress and cancellation for long operations.
4. Complete the real-data benchmark using published Fe₂O₃ coordinates and intensity outputs.
