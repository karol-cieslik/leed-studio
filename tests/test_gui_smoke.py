"""Optional offscreen Qt smoke test; skipped when GUI dependencies are unavailable."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
from PySide6.QtWidgets import QApplication, QFileDialog

from leed_studio.app import MainWindow


def test_window_opens_stack_selects_spot_and_tracks(monkeypatch):
    app = QApplication.instance() or QApplication([])
    project_dir = Path(__file__).resolve().parents[1]
    sample = project_dir / "leed_studio" / "data" / "sample_drifting_stack.tif"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(sample), ""))
    window = MainWindow()
    assert window.advanced_panel.isHidden(), "Advanced controls should be hidden by default for new users"
    assert window.beginner_mode_action.isChecked()
    assert window.centralWidget() is not None
    assert window.data_browser.topLevelItemCount() == 1
    assert window.data_dock.widget() is window.data_browser
    assert window.controls_dock.widget() is not None
    assert window.curve_dock.widget() is not None
    assert window.residual_dock.widget() is not None
    assert window.cursor_position_label is not None
    assert window.fit_button.text() == "Measure spot profile"
    assert window.track_button.text() == "Measure intensity vs energy"
    window.open_image()
    assert window.frames is not None
    assert window.frames.ndim == 3
    assert "simulated" not in window.workflow_banner.text().lower()
    window.select_point(82.0, 77.0)
    window.energy_start.setValue(30.0)
    window.energy_step.setValue(0.5)
    window.energy_confirm.setChecked(True)
    window.run_series()
    assert window.series_result is not None
    assert len(window.series_result) == len(window.frames)
    window.session_dirty = False
    window.close()
    app.processEvents()
