"""Application entry point, including release smoke-test modes."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def _report(message: str) -> None:
    """Report to a console when present, otherwise write a temp log."""
    stream = getattr(sys, "stdout", None) or getattr(sys, "__stdout__", None)
    if stream is not None:
        try:
            print(message, file=stream, flush=True)
            return
        except Exception:
            pass
    try:
        Path(tempfile.gettempdir(), "LEED-Studio-self-test.log").write_text(message + "\n", encoding="utf-8")
    except Exception:
        pass



def _run_core_self_test() -> int:
    """Check numerical dependencies and packaged sample data without requiring Qt."""
    import numpy as np
    from .analysis import fit_spot, load_image_stack, track_spot_series

    sample = Path(__file__).resolve().parent / "data" / "sample_drifting_stack.tif"
    if not sample.is_file():
        raise RuntimeError(f"Bundled example stack is missing: {sample}")
    frames = load_image_stack(sample)
    if frames.ndim != 3 or len(frames) < 2:
        raise RuntimeError(f"Expected a multi-frame TIFF stack, received {frames.shape}.")
    fit, _roi, _model = fit_spot(frames[0], 82.0, 77.0, radius=12)
    if not fit.success or not fit.valid:
        raise RuntimeError(f"Sample spot fit failed validity checks: {fit.message} {fit.validation_flags}")
    energies = 80.0 + 5.0 * np.arange(len(frames))
    points = track_spot_series(
        frames, 82.0, 77.0, energies,
        aperture_radius=5, search_radius=10,
        background_inner_px=7, background_outer_px=10,
        start_frame_index=0, max_displacement_px=3.0,
    )
    if len(points) != len(frames):
        raise RuntimeError("I(E) tracker did not return one point per sample frame.")
    if not any(np.isfinite(point.background_corrected_intensity) for point in points):
        raise RuntimeError("I(E) tracker returned no finite sample intensities.")
    _report(
        f"CORE SELF-TEST PASS: stack={frames.shape}, fit-centre="
        f"({fit.center_x_px:.2f}, {fit.center_y_px:.2f}), I(E) rows={len(points)}."
    )
    return 0


def _run_frozen_gui_self_test() -> int:
    """Exercise the packaged Qt GUI and sample workflow without user interaction."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import numpy as np
    from PySide6.QtWidgets import QApplication
    from .app import MainWindow

    app = QApplication([])
    app.setApplicationName("LEED Studio self-test")
    sample = Path(__file__).resolve().parent / "data" / "sample_drifting_stack.tif"
    if not sample.is_file():
        raise RuntimeError(f"Bundled example stack is missing: {sample}")

    window = MainWindow()
    window.show()
    app.processEvents()
    window._load_image_path(str(sample), is_example=True)
    if window.frames is None or window.frames.ndim != 3 or len(window.frames) < 2:
        raise RuntimeError("Bundled sample stack did not load as a multi-frame stack.")

    # This verifies packaging and core interaction, not scientific validity on
    # experimental data.
    window.select_point(82.0, 77.0)
    window.run_fit()
    if window.fit_result is None or not window.fit_result.success:
        raise RuntimeError("Packaged GUI could not fit the sample spot.")

    window.energy_start.setValue(80.0)
    window.energy_step.setValue(5.0)
    window.energy_confirm.setChecked(True)
    window.run_series()
    if window.series_result is None or len(window.series_result) != len(window.frames):
        raise RuntimeError("Packaged GUI did not produce one I(E) row per frame.")
    if not any(np.isfinite(point.background_corrected_intensity) for point in window.series_result):
        raise RuntimeError("Packaged GUI produced no finite sample intensity values.")

    window.session_dirty = False
    window.close()
    app.processEvents()
    _report("SELF-TEST PASS: Qt window, bundled TIFF, spot fit, I(E) tracking and result table.")
    return 0


def main() -> int:
    if "--self-test-core" in sys.argv:
        try:
            return _run_core_self_test()
        except Exception as exc:
            _report(f"CORE SELF-TEST FAIL: {type(exc).__name__}: {exc}")
            return 2
    if "--self-test-gui" in sys.argv:
        try:
            return _run_frozen_gui_self_test()
        except Exception as exc:
            _report(f"SELF-TEST FAIL: {type(exc).__name__}: {exc}")
            return 2

    from .app import main as run_app
    run_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
