"""Beginner-friendly PySide6 GUI for LEED Studio 0.11.1."""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QUrl, QSettings
from PySide6.QtGui import QAction, QKeySequence, QDesktopServices, QColor, QPen, QIcon
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QSlider, QSpinBox, QSplitter,
    QCheckBox, QComboBox,
    QTabWidget, QVBoxLayout, QWidget, QToolBar, QStatusBar, QMenu, QDialog,
    QDialogButtonBox, QTextBrowser, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QGraphicsEllipseItem, QGraphicsRectItem, QScrollArea, QFrame, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QStyle
)

from .analysis import (
    correct_image_stack, fit_spot, load_image_stack, track_spot_series,
    save_fit_csv, save_series_csv, SpotFit, SeriesPoint
)
from .project_io import save_project, load_project


class ImagePanel(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot = self.addPlot(row=0, col=0)
        self.plot.setAspectLocked(True)
        self.plot.invertY(True)
        self.plot.setLabel("bottom", "x", units="px")
        self.plot.setLabel("left", "y", units="px")
        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)
        self.placeholder = pg.TextItem(
            "No image loaded\nChoose ‘Open data…’ or ‘Try example’", 
            color="#667085", anchor=(0.5, 0.5), fill=pg.mkBrush(255, 255, 255, 220)
        )
        self.placeholder.setPos(0.5, 0.5)
        self.placeholder.setZValue(100)
        self.plot.addItem(self.placeholder)
        self.marker = pg.ScatterPlotItem(size=13, pen=pg.mkPen("y", width=2),
                                         brush=pg.mkBrush(255, 255, 0, 60))
        self.plot.addItem(self.marker)
        self.track_markers = pg.ScatterPlotItem(size=5, pen=pg.mkPen("c", width=1),
                                                brush=pg.mkBrush(0, 200, 220, 160))
        self.plot.addItem(self.track_markers)
        self.current_track_marker = pg.ScatterPlotItem(size=12, pen=pg.mkPen("m", width=2),
                                                        brush=pg.mkBrush(255, 0, 255, 50))
        self.plot.addItem(self.current_track_marker)
        self.aperture_overlay = QGraphicsEllipseItem()
        self.aperture_overlay.setPen(QPen(QColor("#00d084"), 1.5))
        self.aperture_overlay.setZValue(20)
        self.plot.addItem(self.aperture_overlay)
        self.background_inner_overlay = QGraphicsEllipseItem()
        self.background_inner_overlay.setPen(QPen(QColor("#f4c542"), 1.2, Qt.PenStyle.DashLine))
        self.background_inner_overlay.setZValue(19)
        self.plot.addItem(self.background_inner_overlay)
        self.background_outer_overlay = QGraphicsEllipseItem()
        self.background_outer_overlay.setPen(QPen(QColor("#f4c542"), 1.2, Qt.PenStyle.DashLine))
        self.background_outer_overlay.setZValue(19)
        self.plot.addItem(self.background_outer_overlay)
        self.search_overlay = QGraphicsRectItem()
        self.search_overlay.setPen(QPen(QColor("#ff8c42"), 1.2, Qt.PenStyle.DashLine))
        self.search_overlay.setZValue(18)
        self.plot.addItem(self.search_overlay)
        self.set_geometry(None)
        self.click_callback = None
        self.cursor_callback = None
        self.plot.scene().sigMouseClicked.connect(self._on_click)
        self.plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _on_mouse_moved(self, scene_pos):
        if not self.plot.sceneBoundingRect().contains(scene_pos):
            return
        point = self.plot.vb.mapSceneToView(scene_pos)
        if self.cursor_callback:
            self.cursor_callback(float(point.x()), float(point.y()))

    def set_image(self, image, auto_range=False, auto_levels=False):
        self.placeholder.setVisible(False)
        arr = np.asarray(image, dtype=float).copy()
        arr[~np.isfinite(arr)] = 0
        self.image_item.setImage(arr.T, autoLevels=auto_levels)
        if auto_range:
            self.plot.autoRange()

    def set_marker(self, x, y):
        self.marker.setData([{"pos": (x, y)}])

    def set_track_points(self, points, current_index=None):
        valid = [p for p in points if np.isfinite(p.center_x_px) and np.isfinite(p.center_y_px)]
        self.track_markers.setData([{"pos": (p.center_x_px, p.center_y_px)} for p in valid])
        if current_index is not None and 0 <= current_index < len(points):
            p = points[current_index]
            if np.isfinite(p.center_x_px) and np.isfinite(p.center_y_px):
                self.current_track_marker.setData([{"pos": (p.center_x_px, p.center_y_px)}])
            else:
                self.current_track_marker.setData([])
        else:
            self.current_track_marker.setData([])

    def set_geometry(self, center=None, aperture=5, inner=7, outer=10, search=10):
        """Draw the active aperture, background annulus and square search window."""
        visible = (center is not None and len(center) == 2 and
                   np.isfinite(center[0]) and np.isfinite(center[1]))
        for item in (self.aperture_overlay, self.background_inner_overlay,
                     self.background_outer_overlay, self.search_overlay):
            item.setVisible(bool(visible))
        if not visible:
            return
        x, y = float(center[0]), float(center[1])
        for item, radius in ((self.aperture_overlay, aperture),
                             (self.background_inner_overlay, inner),
                             (self.background_outer_overlay, outer)):
            item.setRect(x-radius, y-radius, 2*radius, 2*radius)
        sx, sy = int(round(x)), int(round(y))
        self.search_overlay.setRect(sx-search, sy-search, 2*search+1, 2*search+1)

    def _on_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self.plot.vb.mapSceneToView(event.scenePos())
        x, y = float(point.x()), float(point.y())
        if self.click_callback:
            self.click_callback(x, y)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEED Studio 0.11.1")
        self.resize(1440, 900)
        self.setMinimumSize(980, 620)
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks | QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.GroupedDragging)
        self.raw_frames = None
        self.frames = None
        self.image_path = None
        self.dark_frames = None
        self.flat_frames = None
        self.dark_flat_frames = None
        self.mask_image = None
        self.fit_result = None
        self.fit_frame_index = None
        self.fit_radius_used = None
        self.fit_residual = None
        self.series_result = None
        self.selected = None
        self.session_dirty = False
        self.corrections_dirty = False
        self.corrections_applied = False

        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        open_action = toolbar.addAction("Open data…")
        open_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        open_action.setToolTip("Open a LEED image or a multipage TIFF stack (Ctrl+O).")
        open_action.triggered.connect(self.open_image)
        example_action = toolbar.addAction("Try example")
        example_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        example_action.setToolTip("Open a simulated example stack so you can learn the workflow safely.")
        example_action.triggered.connect(self.open_example)
        toolbar.addSeparator()
        save_project_action = toolbar.addAction("Save project…")
        save_project_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        save_project_action.setToolTip("Save the image, settings and measurements in a LEED Studio project.")
        save_project_action.triggered.connect(self.save_project_dialog)
        load_project_action = toolbar.addAction("Open project…")
        load_project_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        load_project_action.setToolTip("Continue a previously saved LEED Studio project.")
        load_project_action.triggered.connect(self.open_project_dialog)
        toolbar.addSeparator()
        view_curve_action = toolbar.addAction("Show I(E) curve")
        view_curve_action.triggered.connect(lambda: (self.curve_dock.show(), self.curve_dock.raise_()))
        view_tools_action = toolbar.addAction("Show tools")
        view_tools_action.triggered.connect(lambda: (self.controls_dock.show(), self.controls_dock.raise_()))
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Open a LEED image or multipage TIFF stack to begin.")

        self.cursor_position_label = QLabel("Cursor: —")
        self.cursor_position_label.setMinimumWidth(220)
        self.cursor_position_label.setToolTip("Pixel coordinates and raw/working intensity under the cursor.")
        self.image_panel = ImagePanel()
        self.image_panel.click_callback = self.select_point
        self.image_panel.cursor_callback = self.update_cursor_position
        self.curve_plot = pg.PlotWidget(title="Spot intensity versus energy (I(E))")
        self.curve_plot.setLabel("bottom", "Electron energy", units="eV")
        self.curve_plot.setLabel("left", "Estimated spot intensity", units="counts")
        self.curve_plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve_plot.addLegend()
        self.curve_cursor = pg.ScatterPlotItem(
            size=11, pen=pg.mkPen("m", width=2),
            brush=pg.mkBrush(255, 0, 255, 80), name="Current frame"
        )
        self.curve_plot.addItem(self.curve_cursor)
        self.curve_plot.scene().sigMouseClicked.connect(self._on_curve_click)
        self.residual_panel = pg.ImageView()
        self.residual_panel.ui.roiBtn.hide()
        self.residual_panel.ui.menuBtn.hide()

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setAccessibleName("Image frame selector")
        self.frame_slider.setToolTip("Move through the image stack one frame at a time.")
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self.change_frame)
        self.frame_label = QLabel("No stack loaded")

        self.fit_radius = QSpinBox()
        self.fit_radius.setRange(4, 100)
        self.fit_radius.setValue(12)
        self.fit_radius.setSuffix(" px")
        self.aperture_radius = QSpinBox()
        self.aperture_radius.setRange(1, 40)
        self.aperture_radius.setValue(5)
        self.aperture_radius.setSuffix(" px")
        self.search_radius = QSpinBox()
        self.search_radius.setRange(2, 80)
        self.search_radius.setValue(10)
        self.search_radius.setSuffix(" px")
        self.max_displacement = QDoubleSpinBox()
        self.max_displacement.setRange(0.5, 100.0)
        self.max_displacement.setDecimals(2)
        self.max_displacement.setValue(3.0)
        self.max_displacement.setSuffix(" px/frame")
        self.background_inner = QSpinBox()
        self.background_inner.setRange(2, 120)
        self.background_inner.setValue(7)
        self.background_inner.setMinimum(self.aperture_radius.value() + 1)
        self.background_inner.setSuffix(" px")
        self.background_outer = QSpinBox()
        self.background_outer.setRange(3, 140)
        self.background_outer.setValue(10)
        self.background_outer.setMinimum(self.background_inner.value() + 1)
        self.background_outer.setSuffix(" px")
        self.aperture_radius.valueChanged.connect(self._update_background_radii)
        self.background_inner.valueChanged.connect(self._update_background_outer_minimum)
        self.background_inner.valueChanged.connect(self._invalidate_series_for_settings)
        self.background_outer.valueChanged.connect(self._invalidate_series_for_settings)
        self.energy_start = QDoubleSpinBox()
        self.energy_start.setRange(-10000, 100000)
        self.energy_start.setDecimals(3)
        self.energy_start.setValue(0.0)
        self.energy_step = QDoubleSpinBox()
        self.energy_step.setRange(0.001, 10000)
        self.energy_step.setDecimals(3)
        self.energy_step.setValue(1.0)
        self.energy_confirm = QCheckBox("I confirm this energy axis is correct")
        self.energy_confirm.setChecked(False)
        self.energy_start.valueChanged.connect(self._energy_axis_changed)
        self.energy_step.valueChanged.connect(self._energy_axis_changed)
        self.energy_confirm.toggled.connect(self._energy_confirmation_changed)
        self.aperture_radius.valueChanged.connect(self._invalidate_series_for_settings)
        self.search_radius.valueChanged.connect(self._invalidate_series_for_settings)
        self.max_displacement.valueChanged.connect(self._invalidate_series_for_settings)
        self.fit_radius.valueChanged.connect(lambda _value: self.change_frame(self.frame_slider.value()))

        self.fit_button = QPushButton("Measure spot profile")
        self.fit_button.clicked.connect(self.run_fit)
        self.fit_button.setEnabled(False)
        self.fit_button.setMinimumHeight(36)
        self.fit_button.setToolTip("Fit an elliptical Gaussian to the selected spot in the current frame. This is an optional profile measurement.")
        self.track_button = QPushButton("Measure intensity vs energy")
        self.track_button.clicked.connect(self.run_series)
        self.track_button.setEnabled(False)
        self.track_button.setMinimumHeight(36)
        self.track_button.setToolTip("Follow the selected spot through the stack and estimate its intensity in each frame. Set and confirm the energy axis first.")
        self.export_fit_button = QPushButton("Export spot profile…")
        self.export_fit_button.clicked.connect(self.export_fit)
        self.export_fit_button.setEnabled(False)
        self.export_fit_button.setToolTip("Save the current validated spot-profile fit as CSV, with a provenance JSON file.")
        self.export_series_button = QPushButton("Export intensity curve…")
        self.export_series_button.clicked.connect(self.export_series)
        self.export_series_button.setEnabled(False)
        self.export_series_button.setToolTip("Save the measured intensity-versus-energy values and analysis settings.")

        self.results = QLabel("No fit yet. Open a stack and click a spot.")
        self.results.setWordWrap(True)
        self.results.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.correction_info = QLabel("Corrections: none")
        self.correction_info.setWordWrap(True)
        self.correction_info.setStyleSheet("color: #667085;")

        # Histogram/LUT control gives users explicit contrast control without changing
        # the underlying quantitative pixel data.
        self.histogram = pg.HistogramLUTWidget()
        self.histogram.setImageItem(self.image_panel.image_item)
        self.histogram.setMinimumWidth(105)
        image_canvas = QWidget()
        image_canvas_layout = QHBoxLayout(image_canvas)
        image_canvas_layout.setContentsMargins(0, 0, 0, 0)
        image_canvas_layout.addWidget(self.image_panel, stretch=1)
        image_canvas_layout.addWidget(self.histogram)

        image_page = QWidget()
        image_layout = QVBoxLayout(image_page)
        image_layout.addWidget(QLabel("Image viewer — click near the centre of a bright diffraction spot"))
        image_layout.addWidget(self.frame_label)
        image_layout.addWidget(self.frame_slider)
        image_layout.addWidget(self.cursor_position_label)
        image_layout.addWidget(image_canvas, stretch=1)

        self.series_table = QTableWidget(0, 7)
        self.series_table.setHorizontalHeaderLabels(
            ["Frame", "Energy (eV)", "X (px)", "Y (px)", "Corrected intensity", "SNR", "Quality"]
        )
        self.series_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.series_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.series_table.setAlternatingRowColors(True)
        self.series_table.horizontalHeader().setStretchLastSection(True)
        self.series_table.cellClicked.connect(self.select_series_row)

        curve_page = QWidget()
        curve_layout = QVBoxLayout(curve_page)
        curve_layout.addWidget(self.curve_plot, stretch=3)
        curve_layout.addWidget(QLabel("Measurements — click a row or the curve to inspect a frame"))
        warning_nav = QHBoxLayout()
        self.previous_warning_button = QPushButton("Previous flagged frame")
        self.next_warning_button = QPushButton("Next flagged frame")
        self.previous_warning_button.clicked.connect(lambda: self.navigate_warning(-1))
        self.next_warning_button.clicked.connect(lambda: self.navigate_warning(1))
        self.previous_warning_button.setEnabled(False)
        self.next_warning_button.setEnabled(False)
        warning_nav.addWidget(self.previous_warning_button)
        warning_nav.addWidget(self.next_warning_button)
        curve_layout.addLayout(warning_nav)
        curve_layout.addWidget(self.series_table, stretch=2)

        residual_page = QWidget()
        residual_layout = QVBoxLayout(residual_page)
        residual_layout.addWidget(QLabel("Residual image (observed − fitted model)"))
        residual_layout.addWidget(self.residual_panel)

        controls = QWidget()
        controls.setMinimumWidth(260)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        controls_layout.setSpacing(10)

        energy_group = QGroupBox("Energy axis for the curve")
        form = QFormLayout(energy_group)
        form.addRow("Energy of frame 1 (eV)", self.energy_start)
        form.addRow("Energy change per frame (eV)", self.energy_step)
        form.addRow(self.energy_confirm)
        energy_help = QLabel(
            "For a single image, you can ignore this section. For a stack, enter the energy of the first frame "
            "and the step between frames from your experiment metadata. These values are not read from the image."
        )
        energy_help.setWordWrap(True)
        energy_help.setStyleSheet("color: #667085;")
        form.addRow(energy_help)
        self.energy_start.setToolTip("Electron energy assigned to the first image frame. Check your acquisition log.")
        self.energy_step.setToolTip("Energy difference between consecutive frames. Do not assume this is 1 eV unless your acquisition says so.")
        self.energy_confirm.setToolTip("Confirms that you checked the energy start and step against your experiment metadata.")
        self.energy_confirm.setAccessibleName("Confirm energy calibration")
        controls_layout.addWidget(energy_group)

        action_group = QGroupBox("What would you like to do?")
        action_layout = QVBoxLayout(action_group)
        action_layout.addWidget(self.fit_button)
        action_layout.addWidget(self.track_button)
        action_layout.addWidget(self.export_fit_button)
        action_layout.addWidget(self.export_series_button)
        action_help = QLabel(
            "1. Open data and click near a bright spot.\n"
            "2. Choose a measurement.\n"
            "3. Review warnings before exporting."
        )
        action_help.setWordWrap(True)
        action_help.setStyleSheet("color: #667085;")
        action_layout.addWidget(action_help)
        controls_layout.addWidget(action_group)

        self.advanced_toggle = QCheckBox("Show advanced settings")
        self.advanced_toggle.setToolTip("Reveal detector corrections and detailed spot-tracking settings.")
        controls_layout.addWidget(self.advanced_toggle)
        self.advanced_panel = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(8)

        analysis_group = QGroupBox("Detailed measurement settings")
        af = QFormLayout(analysis_group)
        af.addRow("Spot fit area radius", self.fit_radius)
        af.addRow("Spot intensity radius", self.aperture_radius)
        af.addRow("Tracking search radius", self.search_radius)
        af.addRow("Maximum movement per frame", self.max_displacement)
        af.addRow("Background inner radius", self.background_inner)
        af.addRow("Background outer radius", self.background_outer)
        self.fit_radius.setToolTip("Half-width of the region used to fit the spot profile.")
        self.aperture_radius.setToolTip("Radius of the circular area used to estimate spot intensity.")
        self.search_radius.setToolTip("How far from the previous spot centre to search in the next frame.")
        self.max_displacement.setToolTip("Largest allowed spot movement between neighbouring frames. A value that is too small can reject real motion; too large can follow another spot.")
        self.background_inner.setToolTip("Inner radius of the ring used to estimate the local background.")
        self.background_outer.setToolTip("Outer radius of the ring used to estimate the local background.")
        advanced_layout.addWidget(analysis_group)

        correction_group = QGroupBox("Detector corrections (optional)")
        correction_layout = QVBoxLayout(correction_group)
        correction_layout.addWidget(self.correction_info)
        calibration_buttons = QHBoxLayout()
        for label, kind in [("Load dark…", "dark"), ("Load flat…", "flat")]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, k=kind: self.load_aux(k))
            calibration_buttons.addWidget(button)
        correction_layout.addLayout(calibration_buttons)
        calibration_buttons_2 = QHBoxLayout()
        for label, kind in [("Load flat dark…", "darkflat"), ("Load mask…", "mask")]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, k=kind: self.load_aux(k))
            calibration_buttons_2.addWidget(button)
        correction_layout.addLayout(calibration_buttons_2)
        self.calibration_mode = QComboBox()
        self.calibration_mode.addItem("Average into one reference", "average")
        self.calibration_mode.addItem("Match one frame to each image", "framewise")
        self.calibration_mode.setToolTip("Choose based on how the calibration data were acquired. Use synchronized mode only when frames correspond one-to-one.")
        self.calibration_mode.currentIndexChanged.connect(self._calibration_mode_changed)
        correction_layout.addWidget(QLabel("How should calibration stacks be used?"))
        correction_layout.addWidget(self.calibration_mode)
        correction_layout.addWidget(QLabel(
            "Mask convention: white/nonzero pixels are kept; black/zero pixels are excluded. "
            "Corrections change the working image data, not the original. These methods are not identical to ViPErLEED preprocessing."
        ))
        self.apply_corrections_button = QPushButton("Apply selected corrections")
        self.apply_corrections_button.setEnabled(False)
        self.apply_corrections_button.clicked.connect(self.apply_corrections)
        correction_layout.addWidget(self.apply_corrections_button)
        advanced_layout.addWidget(correction_group)
        self.advanced_panel.setVisible(False)
        self.advanced_toggle.toggled.connect(self.advanced_panel.setVisible)
        controls_layout.addWidget(self.advanced_panel)

        results_group = QGroupBox("Result and next step")
        results_layout = QVBoxLayout(results_group)
        results_layout.addWidget(self.results)
        controls_layout.addWidget(results_group)
        controls_layout.addStretch(1)

        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        controls_scroll.setWidget(controls)

        # A Gwyddion-inspired scientific workspace: the image remains central,
        # while data, tools, curves and residuals are persistent dockable panels.
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(5)
        self.workflow_banner = QLabel(
            "WELCOME  ·  1 Open data  →  2 Click a bright spot  →  3 Measure  →  4 Review and export\n"
            "Tip: choose ‘Try example’ first if you want to explore without using your own data."
        )
        self.workflow_banner.setWordWrap(True)
        self.workflow_banner.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.workflow_banner.setStyleSheet(
            "QLabel { background: #eef6ff; color: #183b56; border: 1px solid #c7def5; "
            "border-radius: 6px; padding: 8px 10px; }"
        )
        main_layout.addWidget(self.workflow_banner)
        main_layout.addWidget(image_page, stretch=1)
        self.setCentralWidget(main_container)

        # Data browser: a lightweight project navigator that opens the relevant panel.
        self.data_browser = QTreeWidget()
        self.data_browser.setHeaderHidden(True)
        self.data_browser.setMinimumWidth(210)
        self.data_browser.setAccessibleName("Project data browser")
        self.data_browser.setToolTip("Browse the image stack, calibration inputs and analysis results.")
        self._refresh_data_browser()
        self.data_browser.itemClicked.connect(self._data_browser_activated)
        self.data_dock = self._make_dock("Project", "projectBrowserDock", self.data_browser)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.data_dock)

        self.controls_dock = self._make_dock("Tools & settings", "toolsDock", controls_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.controls_dock)
        self.curve_dock = self._make_dock("Intensity vs energy", "curveDock", curve_page)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.curve_dock)
        self.residual_dock = self._make_dock("Fit residual", "residualDock", residual_page)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.residual_dock)
        self.tabifyDockWidget(self.curve_dock, self.residual_dock)
        self.curve_dock.raise_()

        self.beginner_mode_action = QAction("Beginner mode", self, checkable=True)
        self.beginner_mode_action.setChecked(True)
        self.beginner_mode_action.setToolTip("Hide advanced scientific settings for a simpler workspace.")
        self.beginner_mode_action.toggled.connect(lambda checked: self.advanced_toggle.setChecked(not checked))
        self.advanced_toggle.toggled.connect(lambda checked: self.beginner_mode_action.setChecked(not checked))
        self._build_menus()
        self._install_shortcuts()
        self._restore_workspace()

    def update_cursor_position(self, x, y):
        if self.frames is None:
            self.cursor_position_label.setText(f"Cursor: x {x:.1f} px · y {y:.1f} px")
            return
        frame_index = self.frame_slider.value()
        h, w = self.frames[frame_index].shape
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < w and 0 <= iy < h:
            value = self.frames[frame_index][iy, ix]
            self.cursor_position_label.setText(
                f"x {x:.1f} px · y {y:.1f} px · value {float(value):.5g} · frame {frame_index + 1}"
            )
        else:
            self.cursor_position_label.setText(f"x {x:.1f} px · y {y:.1f} px · outside image")

    def _make_dock(self, title, object_name, widget):
        dock = QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setWidget(widget)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        return dock

    def _refresh_data_browser(self):
        if not hasattr(self, "data_browser"):
            return
        self.data_browser.clear()
        project = QTreeWidgetItem(self.data_browser, ["Project"])
        project.setExpanded(True)
        image_text = self.image_path.name if self.image_path else "No image loaded"
        image_item = QTreeWidgetItem(project, [f"Image stack — {image_text}"])
        image_item.setData(0, Qt.ItemDataRole.UserRole, "image")
        calibration = QTreeWidgetItem(project, ["Detector calibration"])
        calibration.setData(0, Qt.ItemDataRole.UserRole, "calibration")
        calibration.setExpanded(True)
        for label, loaded in (("Dark frame", self.dark_frames is not None),
                              ("Flat field", self.flat_frames is not None),
                              ("Flat-field dark", self.dark_flat_frames is not None),
                              ("Mask", self.mask_image is not None)):
            item = QTreeWidgetItem(calibration, [f"{'✓' if loaded else '○'} {label}"])
            item.setData(0, Qt.ItemDataRole.UserRole, "calibration")
        beam_label = "Selected beam" if self.selected is not None else "No beam selected"
        beam = QTreeWidgetItem(project, [beam_label])
        beam.setData(0, Qt.ItemDataRole.UserRole, "beam")
        if self.selected is not None:
            QTreeWidgetItem(beam, [f"x = {self.selected[0]:.2f} px, y = {self.selected[1]:.2f} px"])
            beam.setExpanded(True)
        curve_label = f"I(E) curve — {len(self.series_result)} frames" if self.series_result else "I(E) curve — not measured"
        curve = QTreeWidgetItem(project, [curve_label])
        curve.setData(0, Qt.ItemDataRole.UserRole, "curve")
        fit_label = "Spot profile — measured" if self.fit_result is not None else "Spot profile — not measured"
        fit = QTreeWidgetItem(project, [fit_label])
        fit.setData(0, Qt.ItemDataRole.UserRole, "fit")
        self.data_browser.expandAll()

    def _data_browser_activated(self, item, column=0):
        if item is None:
            return
        target = item.data(0, Qt.ItemDataRole.UserRole)
        if target == "curve":
            self.curve_dock.show()
            self.curve_dock.raise_()
        elif target == "fit":
            self.residual_dock.show()
            self.residual_dock.raise_()
        elif target == "calibration":
            self.controls_dock.show()
            self.controls_dock.raise_()
            self.advanced_toggle.setChecked(True)
        elif target == "beam":
            self.controls_dock.show()
            self.controls_dock.raise_()
        elif target == "image":
            self.image_panel.setFocus(Qt.FocusReason.OtherFocusReason)

    def _restore_workspace(self):
        settings = QSettings("LEED Studio", "LEED Studio")
        geometry = settings.value("window/geometry")
        state = settings.value("window/state")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)
        else:
            self.resizeDocks([self.data_dock, self.controls_dock], [230, 320], Qt.Orientation.Horizontal)
            self.resizeDocks([self.curve_dock], [250], Qt.Orientation.Vertical)

    def reset_workspace_layout(self):
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.data_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.controls_dock)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.curve_dock)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.residual_dock)
        self.tabifyDockWidget(self.curve_dock, self.residual_dock)
        self.data_dock.show()
        self.controls_dock.show()
        self.curve_dock.show()
        self.curve_dock.raise_()
        self.resizeDocks([self.data_dock, self.controls_dock], [230, 320], Qt.Orientation.Horizontal)
        self.resizeDocks([self.curve_dock], [250], Qt.Orientation.Vertical)
        self.statusBar().showMessage("Workspace layout reset.")

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open data…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        example_action = QAction("Try &example data", self)
        example_action.triggered.connect(self.open_example)
        file_menu.addAction(example_action)
        file_menu.addSeparator()
        open_project_action = QAction("Open &project…", self)
        open_project_action.triggered.connect(self.open_project_dialog)
        file_menu.addAction(open_project_action)
        save_project_action = QAction("&Save project…", self)
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        save_project_action.triggered.connect(self.save_project_dialog)
        file_menu.addAction(save_project_action)
        file_menu.addSeparator()

        export_fit_action = QAction("Export fit CSV…", self)
        export_fit_action.setShortcut("Ctrl+Shift+E")
        export_fit_action.triggered.connect(self.export_fit)
        file_menu.addAction(export_fit_action)
        export_curve_action = QAction("Export I(E) CSV…", self)
        export_curve_action.setShortcut("Ctrl+E")
        export_curve_action.triggered.connect(self.export_series)
        file_menu.addAction(export_curve_action)
        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.beginner_mode_action)
        view_menu.addSeparator()
        for dock in (self.data_dock, self.controls_dock, self.curve_dock, self.residual_dock):
            view_menu.addAction(dock.toggleViewAction())
        layout_action = QAction("Reset workspace layout", self)
        layout_action.triggered.connect(self.reset_workspace_layout)
        view_menu.addAction(layout_action)
        view_menu.addSeparator()
        reset_action = QAction("Reset image zoom", self)
        reset_action.setShortcut("Ctrl+0")
        reset_action.triggered.connect(self.reset_image_view)
        view_menu.addAction(reset_action)
        first_action = QAction("First frame", self)
        first_action.setShortcut("Home")
        first_action.triggered.connect(lambda: self.frame_slider.setValue(0))
        view_menu.addAction(first_action)
        last_action = QAction("Last frame", self)
        last_action.setShortcut("End")
        last_action.triggered.connect(lambda: self.frame_slider.setValue(self.frame_slider.maximum()))
        view_menu.addAction(last_action)

        analysis_menu = self.menuBar().addMenu("&Analysis")
        fit_action = QAction("Fit selected spot", self)
        fit_action.setShortcut("F")
        fit_action.triggered.connect(self.run_fit)
        analysis_menu.addAction(fit_action)
        track_action = QAction("Track spot and measure I(E)", self)
        track_action.setShortcut("T")
        track_action.triggered.connect(self.run_series)
        analysis_menu.addAction(track_action)

        help_menu = self.menuBar().addMenu("&Help")
        guide_action = QAction("Quick start guide…", self)
        guide_action.setShortcut("F1")
        guide_action.triggered.connect(self.show_quick_guide)
        help_menu.addAction(guide_action)
        help_menu.addSeparator()
        about_action = QAction("About LEED Studio", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        benchmark_action = QAction("Public benchmark dataset…", self)
        benchmark_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://doi.org/10.48436/hgg42-xss85"))
        )
        help_menu.addAction(benchmark_action)
        docs_action = QAction("ViPErLEED ImageJ documentation…", self)
        docs_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.viperleed.org/stable/content/imagej_plugins.html"))
        )
        help_menu.addAction(docs_action)

    def _install_shortcuts(self):
        # Arrow keys navigate frames even when the image viewer has focus.
        previous = QAction(self)
        previous.setShortcut(QKeySequence.StandardKey.MoveToPreviousChar)
        previous.triggered.connect(lambda: self.frame_slider.setValue(max(0, self.frame_slider.value()-1)))
        self.addAction(previous)
        next_frame = QAction(self)
        next_frame.setShortcut(QKeySequence.StandardKey.MoveToNextChar)
        next_frame.triggered.connect(
            lambda: self.frame_slider.setValue(min(self.frame_slider.maximum(), self.frame_slider.value()+1))
        )
        self.addAction(next_frame)

    def reset_image_view(self):
        self.image_panel.plot.autoRange()
        self.statusBar().showMessage("Image view reset.")

    def show_about(self):
        QMessageBox.about(
            self, "About LEED Studio",
            "<h3>LEED Studio 0.11.1</h3>"
            "<p>Standalone prototype for LEED image inspection, spot-profile fitting, "
            "detector correction and exploratory I(E) extraction.</p>"
            "<p><b>Scientific status:</b> the tracker is a baseline algorithm, not a "
            "reimplementation of the ViPErLEED Spot Tracker. Validate settings and "
            "results against reference data before using them for publication.</p>"
            "<p>Public benchmark: TU Wien dataset DOI 10.48436/hgg42-xss85.</p>"
        )

    def open_image(self):
        if not self._confirm_discard_session():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open LEED image or multipage TIFF", "",
            "Images (*.tif *.tiff *.png *.jpg *.jpeg *.bmp);;All files (*.*)"
        )
        if not path:
            return
        self._load_image_path(path)

    def open_example(self):
        """Open included simulated data to let first-time users practise safely."""
        if not self._confirm_discard_session():
            return
        path = Path(__file__).resolve().parent / "data" / "sample_drifting_stack.tif"
        if not path.exists():
            QMessageBox.warning(self, "Example not found", "The example stack is missing. Re-extract the complete LEED Studio folder.")
            return
        self._load_image_path(str(path), is_example=True)

    def _load_image_path(self, path, is_example=False):
        try:
            frames = load_image_stack(path)
        except Exception as exc:
            QMessageBox.critical(self, "Could not open image", str(exc))
            return
        self.raw_frames = frames
        self.frames = frames
        self.image_path = Path(path)
        self.setWindowTitle(f"LEED Studio 0.11.1 — {self.image_path.name}")
        self.dark_frames = self.flat_frames = self.dark_flat_frames = self.mask_image = None
        self.corrections_dirty = False
        self.corrections_applied = False
        self.energy_confirm.setChecked(False)
        self.fit_result = self.series_result = None
        self.fit_frame_index = self.fit_radius_used = None
        self.fit_residual = None
        self.selected = None
        self.session_dirty = False
        self.frame_slider.blockSignals(True)
        self.frame_slider.setRange(0, len(frames)-1)
        self.frame_slider.setValue(0)
        self.frame_slider.blockSignals(False)
        self.image_panel.set_track_points([])
        self.image_panel.marker.setData([])
        self.fit_button.setEnabled(False)
        self.track_button.setEnabled(False)
        self.export_fit_button.setEnabled(False)
        self.export_series_button.setEnabled(False)
        self.apply_corrections_button.setEnabled(False)
        self.curve_plot.clear()
        self.curve_plot.addLegend()
        self.curve_plot.addItem(self.curve_cursor)
        self.curve_cursor.setData([])
        self.series_table.setRowCount(0)
        self.residual_panel.clear()
        self.image_panel.set_image(frames[0], auto_range=True, auto_levels=True)
        self.frame_label.setText(f"Frame 1 of {len(frames)} · energy axis not confirmed")
        self.results.setText("Next: click near the centre of a bright diffraction spot in the image.")
        self.correction_info.setText("No corrections loaded.")
        self.workflow_banner.setText(
            ("EXAMPLE DATA  ·  This is simulated data for practising the workflow, not an experimental result.\n"
             "Click the bright spot, then choose ‘Measure spot profile’ or ‘Measure intensity vs energy’."
             if is_example else
             "DATA LOADED  ·  Click near the centre of a bright spot. Then choose a measurement on the right.\n"
             "For I(E), check the first energy and energy step against your experiment metadata before confirming the axis.")
        )
        self.statusBar().showMessage(
            f"Loaded {len(frames)} frame(s) · {frames.shape[2]} × {frames.shape[1]} px · {self.image_path.name}"
        )
        self.change_frame(0)
        self._refresh_data_browser()

    def show_quick_guide(self):
        QMessageBox.information(
            self, "LEED Studio — quick start",
            "<h3>Start in four steps</h3>"
            "<ol><li><b>Open data</b> — choose a grayscale image or multipage TIFF stack. Use ‘Try example’ to practise with simulated data.</li>"
            "<li><b>Select a spot</b> — click near the centre of a bright diffraction spot in the image.</li>"
            "<li><b>Measure</b> — use ‘Measure spot profile’ for one frame, or ‘Measure intensity vs energy’ for a stack. The curve and fit residual open in dockable panels.</li>"
            "<li><b>Review and save</b> — inspect warnings and flagged frames, save a .leedproj project, then export CSV data.</li></ol>"
            "<p><b>Before I(E):</b> enter the real energy of frame 1 and the step between frames from your acquisition metadata, then confirm the axis.</p>"
            "<p><b>Workspace:</b> use the Project browser to open panels, drag panel title bars to rearrange them, or use View → Reset workspace layout. The layout is remembered when you close the app.</p>"
            "<p><b>Scientific caution:</b> this is exploratory software. Check results against reference data before using them in a publication.</p>"
        )

    def load_aux(self, kind):
        if self.raw_frames is None:
            QMessageBox.information(self, "Load LEED data first", "Open the main LEED image or stack first.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, f"Load {kind} image or stack", "",
            "Images (*.tif *.tiff *.png *.bmp);;All files (*.*)"
        )
        if not path:
            return
        try:
            arr = load_image_stack(path)
            if arr.shape[1:] != self.raw_frames.shape[1:]:
                raise ValueError("Calibration image dimensions must match the main LEED image.")
            if kind == "dark":
                self.dark_frames = arr
            elif kind == "flat":
                self.flat_frames = arr
            elif kind == "darkflat":
                self.dark_flat_frames = arr
            elif kind == "mask":
                self.mask_image = arr[0]
            self.session_dirty = True
            self.corrections_dirty = True
            self._clear_measurements_for_preprocessing_change()
            self.apply_corrections_button.setEnabled(any(x is not None for x in (self.dark_frames, self.flat_frames, self.dark_flat_frames, self.mask_image)))
            self.correction_info.setText(
                f"Dark: {'loaded' if self.dark_frames is not None else 'none'} · "
                f"Flat: {'loaded' if self.flat_frames is not None else 'none'} · "
                f"Flat dark: {'loaded' if self.dark_flat_frames is not None else 'none'} · "
                f"Mask: {'loaded' if self.mask_image is not None else 'none'}"
            )
            self._refresh_data_browser()
            self.statusBar().showMessage(f"Loaded {kind} calibration: {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Could not load calibration", str(exc))

    def apply_corrections(self):
        if self.raw_frames is None:
            return
        try:
            self.frames = correct_image_stack(
                self.raw_frames, dark=self.dark_frames, flat=self.flat_frames,
                dark_for_flat=self.dark_flat_frames, mask=self.mask_image,
                calibration_mode=str(self.calibration_mode.currentData())
            )
        except Exception as exc:
            QMessageBox.critical(self, "Correction failed", str(exc))
            return
        self.corrections_dirty = False
        self.apply_corrections_button.setEnabled(False)
        self.corrections_applied = any(x is not None for x in
                                        (self.dark_frames, self.flat_frames, self.dark_flat_frames, self.mask_image))
        self.series_result = None
        self.fit_result = None
        self.fit_frame_index = self.fit_radius_used = None
        self.fit_residual = None
        self.session_dirty = True
        self.image_panel.set_image(self.frames[self.frame_slider.value()], auto_levels=True)
        self.image_panel.set_track_points([])
        self.curve_plot.clear()
        self.curve_plot.addItem(self.curve_cursor)
        self.curve_cursor.setData([])
        self.series_table.setRowCount(0)
        self.export_fit_button.setEnabled(False)
        self.export_series_button.setEnabled(False)
        self.correction_info.setText(
            "Preprocessing applied to working copy. Original stack retained in memory. "
            f"Calibration mode: {self.calibration_mode.currentText()}. "
            "This is a normalized flat-field correction, not the ViPErLEED polynomial correction."
        )
        self._refresh_data_browser()
        self.statusBar().showMessage("Preprocessing applied. Verify correction settings before measurement.")

    def _energy_axis_changed(self, _value):
        # Any change to the numerical axis invalidates the user's previous confirmation.
        self.energy_confirm.setChecked(False)
        self._invalidate_series_for_settings(_value)

    def _energy_confirmation_changed(self, checked):
        if not checked:
            self._invalidate_series_for_settings(False)
            if self.raw_frames is not None:
                self.workflow_banner.setText(
                    "ENERGY AXIS NEEDS CONFIRMATION  ·  Check the first-frame energy and energy step against your acquisition metadata, then confirm before measuring I(E)."
                )
        elif self.raw_frames is not None:
            self.change_frame(self.frame_slider.value())
            self.workflow_banner.setText("ENERGY AXIS CONFIRMED  ·  Click a spot if you have not selected one, then choose ‘Measure intensity vs energy’. Review flagged frames before export.")
            self.statusBar().showMessage(
                f"Energy axis confirmed: {self.energy_start.value():g} eV, "
                f"step {self.energy_step.value():g} eV/frame."
            )

    def _calibration_mode_changed(self, _index):
        if self.raw_frames is not None and any(x is not None for x in
                (self.dark_frames, self.flat_frames, self.dark_flat_frames, self.mask_image)):
            self.apply_corrections_button.setEnabled(True)
            self.corrections_dirty = True
            self.session_dirty = True
            self._clear_measurements_for_preprocessing_change()
            self.correction_info.setText(
                "Calibration mode changed; re-apply corrections before measuring again."
            )

    def _clear_measurements_for_preprocessing_change(self):
        """Prevent old results from being exported under a changed preprocessing setup."""
        self.fit_result = None
        self.fit_frame_index = self.fit_radius_used = None
        self.fit_residual = None
        self.series_result = None
        self.export_fit_button.setEnabled(False)
        self.export_series_button.setEnabled(False)
        self.previous_warning_button.setEnabled(False)
        self.next_warning_button.setEnabled(False)
        self.image_panel.set_track_points([])
        self.curve_plot.clear()
        self.curve_plot.addLegend()
        self.curve_plot.addItem(self.curve_cursor)
        self.curve_cursor.setData([])
        self.series_table.setRowCount(0)
        self.residual_panel.clear()
        if self.selected is not None:
            self.results.setText("Preprocessing changed. Apply corrections, then repeat the spot analysis.")

    def _update_background_radii(self, aperture_value):
        minimum_inner = int(aperture_value) + 1
        self.background_inner.setMinimum(minimum_inner)
        if self.background_inner.value() < minimum_inner:
            self.background_inner.setValue(minimum_inner + 1)
        self._update_background_outer_minimum(self.background_inner.value())

    def _update_background_outer_minimum(self, inner_value):
        minimum_outer = int(inner_value) + 1
        self.background_outer.setMinimum(minimum_outer)
        if self.background_outer.value() < minimum_outer:
            self.background_outer.setValue(minimum_outer + 2)

    def _invalidate_series_for_settings(self, _value):
        if self.series_result:
            self.series_result = None
            self.export_series_button.setEnabled(False)
            self.previous_warning_button.setEnabled(False)
            self.next_warning_button.setEnabled(False)
            self.image_panel.set_track_points([])
            self.curve_plot.clear()
            self.curve_plot.addLegend()
            self.curve_plot.addItem(self.curve_cursor)
            self.curve_cursor.setData([])
            self.series_table.setRowCount(0)
            self.results.setText("I(E) results cleared because measurement settings changed. Re-run tracking to create a curve with the new settings.")
        if self.raw_frames is not None:
            self.session_dirty = True

    def _on_curve_click(self, event):
        if not self.series_result:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self.curve_plot.plotItem.vb.mapSceneToView(event.scenePos())
        energies = np.asarray([p.energy_ev for p in self.series_result], dtype=float)
        finite = np.isfinite(energies)
        if not finite.any():
            return
        candidates = np.flatnonzero(finite)
        row = int(candidates[np.argmin(np.abs(energies[finite] - point.x()))])
        self.frame_slider.setValue(row)

    def navigate_warning(self, direction: int):
        if not self.series_result:
            return
        flagged = [i for i, p in enumerate(self.series_result)
                   if p.quality_flag != "ok" and p.quality_flag != "unchecked"]
        if not flagged:
            self.statusBar().showMessage("No flagged frames in the current measurement.")
            return
        current = self.frame_slider.value()
        if direction > 0:
            target = next((i for i in flagged if i > current), flagged[0])
        else:
            target = next((i for i in reversed(flagged) if i < current), flagged[-1])
        self.frame_slider.setValue(target)

    def _confirm_discard_session(self) -> bool:
        if self.raw_frames is None or not self.session_dirty:
            return True
        box = QMessageBox(self)
        box.setWindowTitle("Unsaved analysis")
        box.setText("This session has changes that have not been saved.")
        box.setInformativeText("Save the project before continuing?")
        save_button = box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard_button = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(save_button)
        box.exec()
        clicked = box.clickedButton()
        if clicked == save_button:
            return self.save_project_dialog()
        if clicked == discard_button:
            return True
        return False

    def closeEvent(self, event):
        if self._confirm_discard_session():
            settings = QSettings("LEED Studio", "LEED Studio")
            settings.setValue("window/geometry", self.saveGeometry())
            settings.setValue("window/state", self.saveState())
            event.accept()
        else:
            event.ignore()

    def _update_geometry_overlay(self, index):
        center = self.selected
        if self.series_result and 0 <= index < len(self.series_result):
            point = self.series_result[index]
            center = ((point.center_x_px, point.center_y_px)
                      if np.isfinite(point.center_x_px) and np.isfinite(point.center_y_px) else None)
        self.image_panel.set_geometry(
            center, aperture=self.aperture_radius.value(),
            inner=self.background_inner.value(), outer=self.background_outer.value(),
            search=self.search_radius.value())

    def change_frame(self, index):
        if self.frames is None:
            return
        self.image_panel.set_image(self.frames[index])
        if self.energy_confirm.isChecked():
            energy = self.energy_start.value() + self.energy_step.value() * index
            self.frame_label.setText(f"Frame {index+1} of {len(self.frames)} · {energy:g} eV (confirmed axis)")
        else:
            self.frame_label.setText(f"Frame {index+1} of {len(self.frames)} · energy axis not confirmed")
        if self.fit_result is not None:
            current_fit = (self.fit_frame_index == index and
                           self.fit_radius_used == self.fit_radius.value())
            self.export_fit_button.setEnabled(bool(current_fit and self.fit_result.success))
            base_text = self.results.text().split("\n\n[STALE CONTEXT]")[0]
            if current_fit:
                self.results.setText(base_text)
            else:
                reason = (f"frame {self.fit_frame_index + 1}" if self.fit_frame_index != index
                          else f"fit radius {self.fit_radius_used} px")
                self.results.setText(base_text +
                    f"\n\n[STALE CONTEXT] Fit was calculated with {reason}; "
                    "restore the original context to export it.")
        if self.series_result:
            self.image_panel.set_track_points(self.series_result, index)
            point = self.series_result[index]
            if np.isfinite(point.background_corrected_intensity):
                self.curve_cursor.setData([{"pos": (point.energy_ev, point.background_corrected_intensity)}])
            else:
                self.curve_cursor.setData([])
            self.series_table.blockSignals(True)
            self.series_table.selectRow(index)
            self.series_table.blockSignals(False)
        else:
            self.curve_cursor.setData([])
            if self.selected is not None:
                self.image_panel.set_marker(*self.selected)
        self._update_geometry_overlay(index)

    def select_series_row(self, row, column):
        if self.frames is not None and 0 <= row < len(self.frames):
            self.frame_slider.setValue(row)

    def select_point(self, x, y):
        if self.frames is None:
            return
        h, w = self.frames[self.frame_slider.value()].shape
        if x < 0 or y < 0 or x >= w or y >= h:
            return
        self.selected = (x, y)
        # A new spot invalidates any previous fit/curve so stale results cannot be
        # accidentally exported under a newly selected location.
        self.fit_result = None
        self.fit_frame_index = self.fit_radius_used = None
        self.fit_residual = None
        self.series_result = None
        self.session_dirty = True
        self.export_fit_button.setEnabled(False)
        self.export_series_button.setEnabled(False)
        self.image_panel.set_track_points([])
        self.image_panel.set_marker(x, y)
        self._update_geometry_overlay(self.frame_slider.value())
        self.curve_plot.clear()
        self.curve_cursor = pg.ScatterPlotItem(
            size=11, pen=pg.mkPen("m", width=2),
            brush=pg.mkBrush(255, 0, 255, 80), name="Current frame"
        )
        self.curve_plot.addItem(self.curve_cursor)
        self.series_table.setRowCount(0)
        self.residual_panel.clear()
        self.fit_button.setEnabled(True)
        self.track_button.setEnabled(len(self.frames) > 1)
        self.results.setText("Spot selected. Run a fit or track the spot through the stack.")
        self._refresh_data_browser()
        self.workflow_banner.setText("SPOT SELECTED  ·  Choose ‘Measure spot profile’ for the current frame or set the energy axis and choose ‘Measure intensity vs energy’ for the full stack.")
        self.statusBar().showMessage(f"Selected spot at ({x:.1f}, {y:.1f}) px in frame {self.frame_slider.value()+1}.")

    def run_fit(self):
        if self.frames is None or self.selected is None:
            return
        idx = self.frame_slider.value()
        try:
            fit, roi, model = fit_spot(self.frames[idx], *self.selected, radius=self.fit_radius.value())
        except Exception as exc:
            QMessageBox.warning(self, "Fit failed", str(exc))
            return
        self.fit_result = fit
        self.fit_frame_index = idx
        self.fit_radius_used = self.fit_radius.value()
        self.fit_residual = roi - model
        self.session_dirty = True
        self.residual_panel.setImage(self.fit_residual.T, autoLevels=True)
        self.results.setText(
            f"Fit valid: {fit.valid} · optimizer converged: {fit.optimizer_success} · source frame: {idx + 1}\n"
            f"Centre: ({fit.center_x_px:.2f}, {fit.center_y_px:.2f}) px\n"
            f"Amplitude: {fit.amplitude:.4g}\nBackground: {fit.background:.4g}\n"
            f"FWHM: {fit.fwhm_x_px:.3f} × {fit.fwhm_y_px:.3f} px\n"
            f"Angle: {fit.angle_deg:.2f}°\nIntegrated fitted signal: {fit.integrated_gaussian_counts:.5g}\n"
            f"RMSE: {fit.rmse:.5g} · R²: {fit.r_squared:.5f} · fit SNR: {fit.fit_snr:.3g}\n"
            f"Centre SE (diagnostic): {fit.center_x_std_px:.3g}, {fit.center_y_std_px:.3g} px\n"
            f"Valid pixels: {fit.n_valid_pixels} · optimizer converged: {fit.optimizer_success}\n"
            f"Validation: {fit.validation_flags or 'passed'}\n{fit.message}"
        )
        self.export_fit_button.setEnabled(bool(fit.success))
        self._refresh_data_browser()
        self.residual_dock.show()
        self.residual_dock.raise_()
        self.workflow_banner.setText("SPOT PROFILE COMPLETE  ·  Check the validity message and residual image. Export is enabled only when the fit passes validity checks.")
        if fit.success:
            self.statusBar().showMessage("Fit passed validity checks. Inspect residuals; uncertainty values are model-based diagnostics.")
        else:
            self.statusBar().showMessage(
                "Fit rejected by validity checks; inspect the validation flags. "
                "The numerical optimizer may still have converged. Export is disabled."
            )

    def run_series(self):
        if self.frames is None or self.selected is None:
            return
        if not self.energy_confirm.isChecked():
            QMessageBox.warning(
                self, "Confirm energy calibration",
                "The energy axis is currently an assumption. Enter the correct first energy and step, "
                "then tick 'I confirm this energy axis is correct' before measuring I(E)."
            )
            return
        energies = self.energy_start.value() + self.energy_step.value() * np.arange(len(self.frames))
        try:
            points = track_spot_series(
                self.frames, *self.selected, energies,
                aperture_radius=self.aperture_radius.value(),
                search_radius=self.search_radius.value(),
                background_inner_px=self.background_inner.value(),
                background_outer_px=self.background_outer.value(),
                start_frame_index=self.frame_slider.value(),
                max_displacement_px=self.max_displacement.value()
            )
        except Exception as exc:
            QMessageBox.warning(self, "I(E) measurement failed", str(exc))
            return
        self.series_result = points
        self.session_dirty = True
        self.image_panel.set_track_points(points, self.frame_slider.value())
        self._update_geometry_overlay(self.frame_slider.value())
        self.series_table.setRowCount(len(points))
        for row, point in enumerate(points):
            values = [
                str(point.frame_index + 1),
                f"{point.energy_ev:.4f}",
                f"{point.center_x_px:.3f}",
                f"{point.center_y_px:.3f}",
                f"{point.background_corrected_intensity:.6g}",
                f"{point.signal_to_noise_ratio:.3g}",
                point.quality_flag,
            ]
            for col, value in enumerate(values):
                self.series_table.setItem(row, col, QTableWidgetItem(value))
        self.series_table.selectRow(self.frame_slider.value())
        x = np.array([p.energy_ev for p in points])
        y = np.array([p.background_corrected_intensity for p in points])
        self.curve_plot.clear()
        self.curve_plot.addLegend()
        self.curve_plot.addItem(self.curve_cursor)
        self.curve_plot.plot(x, y, pen=pg.mkPen("c", width=2), symbol="o",
                             symbolSize=5, symbolBrush=pg.mkBrush("c"), name="Tracked spot")
        current = points[self.frame_slider.value()]
        self.curve_cursor.setData([{"pos": (current.energy_ev, current.background_corrected_intensity)}])
        failed = sum(p.quality_flag.startswith("failed:") for p in points)
        invalid_intensity = sum(not np.isfinite(p.background_corrected_intensity) for p in points)
        self.export_series_button.setEnabled(True)
        has_flags = any(p.quality_flag not in {"ok", "unchecked"} for p in points)
        self.previous_warning_button.setEnabled(has_flags)
        self.next_warning_button.setEnabled(has_flags)
        self.curve_dock.show()
        self.curve_dock.raise_()
        self.workflow_banner.setText("I(E) MEASUREMENT COMPLETE  ·  Review flagged frames using the navigation buttons, then save the project and export the curve. This exploratory method is not yet validated as equivalent to ViPErLEED.")
        self.statusBar().showMessage(
            f"Processed {len(points)} frames: {failed} tracking failures, {invalid_intensity} invalid intensities. "
            "Review flagged rows before using the curve."
        )

    def _project_metadata(self):
        return {
            "software": "LEED Studio",
            "software_version": "0.11.1",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "measurement_method": "local maximum + intensity centroid; circular aperture with median annular background",
            "mask_convention": "nonzero=keep; zero=exclude",
            "working_is_raw": self.frames is self.raw_frames,
            "corrections_dirty": self.corrections_dirty,
            "corrections_applied": self.corrections_applied,
            "calibration_mode": str(self.calibration_mode.currentData()),
            "energy_axis_confirmed": self.energy_confirm.isChecked(),
            "source_path": str(self.image_path) if self.image_path else None,
            "frame_index": int(self.frame_slider.value()),
            "selected": list(self.selected) if self.selected is not None else None,
            "settings": {
                "energy_start": self.energy_start.value(),
                "energy_step": self.energy_step.value(),
                "fit_radius": self.fit_radius.value(),
                "aperture_radius": self.aperture_radius.value(),
                "search_radius": self.search_radius.value(),
                "max_displacement": self.max_displacement.value(),
                "background_inner": self.background_inner.value(),
                "background_outer": self.background_outer.value(),
            },
            "fit_result": self.fit_result.to_dict() if self.fit_result else None,
            "fit_frame_index": self.fit_frame_index,
            "fit_radius_used": self.fit_radius_used,
            "series_result": [p.to_dict() for p in self.series_result] if self.series_result else None,
        }

    def save_project_dialog(self):
        if self.raw_frames is None:
            QMessageBox.information(self, "Nothing to save", "Open a LEED image or stack first.")
            return
        suggested = (self.image_path.stem if self.image_path else "leed_studio") + ".leedproj"
        path, _ = QFileDialog.getSaveFileName(self, "Save LEED Studio project", suggested,
                                              "LEED Studio project (*.leedproj)")
        if not path:
            return False
        if not path.lower().endswith(".leedproj"):
            path += ".leedproj"
        arrays = {
            "raw_frames": self.raw_frames,
            "frames": None if self.frames is self.raw_frames else self.frames,
            "dark_frames": self.dark_frames, "flat_frames": self.flat_frames,
            "dark_flat_frames": self.dark_flat_frames, "mask_image": self.mask_image,
            "fit_residual": self.fit_residual,
        }
        try:
            save_project(path, arrays, self._project_metadata())
            self.session_dirty = False
            self.statusBar().showMessage(f"Saved self-contained project: {path}")
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Could not save project", str(exc))
            return False

    def open_project_dialog(self):
        if not self._confirm_discard_session():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open LEED Studio project", "",
                                              "LEED Studio project (*.leedproj)")
        if not path:
            return
        try:
            arrays, metadata = load_project(path)
            raw = arrays.get("raw_frames")
            working = arrays.get("frames")
            if working is None and metadata.get("working_is_raw"):
                working = raw
            if raw is None or working is None or raw.ndim != 3 or working.shape != raw.shape:
                raise ValueError("Project does not contain compatible raw and working image stacks.")
            if raw.dtype.kind not in "iuf" or not np.isfinite(raw).all():
                raise ValueError("Project raw stack must contain finite numeric pixels.")
            if working.dtype.kind not in "iuf" or np.isinf(working).any():
                raise ValueError("Project working stack must contain numeric pixels without infinities.")
            selected = metadata.get("selected")
            settings = metadata.get("settings", {})
            fit_data = metadata.get("fit_result")
            series_data = metadata.get("series_result")
            if not isinstance(settings, dict):
                raise ValueError("Project settings must be an object.")
            setting_ranges = {
                "energy_start": (-10000.0, 100000.0), "energy_step": (0.001, 10000.0),
                "fit_radius": (4, 100), "aperture_radius": (1, 40), "search_radius": (2, 80),
                "max_displacement": (0.5, 100),
                "background_inner": (2, 120), "background_outer": (3, 140),
            }
            for key, value in settings.items():
                if key not in setting_ranges:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                    raise ValueError(f"Project setting {key!r} must be a finite number.")
                lo, hi = setting_ranges[key]
                if not lo <= value <= hi:
                    raise ValueError(f"Project setting {key!r} is outside the supported range.")
            aperture_candidate = settings.get("aperture_radius", self.aperture_radius.value())
            inner_candidate = settings.get("background_inner", self.background_inner.value())
            outer_candidate = settings.get("background_outer", self.background_outer.value())
            if inner_candidate <= aperture_candidate or outer_candidate <= inner_candidate:
                raise ValueError("Project background annulus must be outside the intensity aperture.")
            try:
                index_candidate = int(metadata.get("frame_index", 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("Project frame index must be an integer.") from exc
            if not 0 <= index_candidate < len(raw):
                raise ValueError("Project frame index is outside the image stack.")
            h, w = raw.shape[1:]
            for name in ("dark_frames", "flat_frames", "dark_flat_frames"):
                arr = arrays.get(name)
                if arr is not None and (arr.ndim not in (2, 3) or arr.shape[-2:] != (h, w)):
                    raise ValueError(f"Project calibration {name!r} has incompatible dimensions.")
                if arr is not None and (arr.ndim == 3 and arr.shape[0] < 1 or not np.isfinite(arr).all()):
                    raise ValueError(f"Project calibration {name!r} contains invalid pixels.")
            mask_candidate = arrays.get("mask_image")
            if mask_candidate is not None and mask_candidate.shape != (h, w):
                raise ValueError("Project mask dimensions do not match the image stack.")
            if mask_candidate is not None and not np.isfinite(mask_candidate).all():
                raise ValueError("Project mask contains non-finite values.")
            residual_candidate = arrays.get("fit_residual")
            if residual_candidate is not None and residual_candidate.ndim != 2:
                raise ValueError("Project fit residual must be a 2D image.")
            selected_candidate = None
            if selected is not None:
                if not isinstance(selected, (list, tuple)) or len(selected) != 2:
                    raise ValueError("Project selected spot must contain x and y coordinates.")
                selected_candidate = tuple(float(v) for v in selected)
                if not all(np.isfinite(v) for v in selected_candidate):
                    raise ValueError("Project selected spot coordinates must be finite.")
                if not (0 <= selected_candidate[0] < w and 0 <= selected_candidate[1] < h):
                    raise ValueError("Project selected spot is outside the image.")
            fit_candidate = None
            fit_frame_candidate = metadata.get("fit_frame_index")
            fit_radius_candidate = metadata.get("fit_radius_used")
            if fit_data:
                fit_data = {k: (float("nan") if v is None else v) for k, v in fit_data.items()}
                fit_candidate = SpotFit(**fit_data)
                # 0.8.x projects predate explicit scientific fit validation. Do not
                # silently trust their old optimizer-only success flag.
                if "valid" not in fit_data and fit_candidate.success:
                    fit_candidate.success = False
                    fit_candidate.valid = False
                    fit_candidate.validation_flags = "legacy fit not scientifically revalidated"
                    fit_candidate.message = (fit_candidate.message + "; legacy fit requires re-fitting")
                if fit_frame_candidate is None:
                    fit_frame_candidate = int(metadata.get("frame_index", 0))
                if not 0 <= int(fit_frame_candidate) < len(raw):
                    raise ValueError("Project fit source frame is outside the image stack.")
                if fit_radius_candidate is None:
                    fit_radius_candidate = int(settings.get("fit_radius", self.fit_radius.value()))
            series_candidate = None
            if series_data:
                if not isinstance(series_data, list) or len(series_data) != len(raw):
                    raise ValueError("Project I(E) result must contain one row per source frame.")
                series_candidate = [SeriesPoint(**{
                    k: (float("nan") if v is None and k in {
                        "signal_to_noise_ratio", "displacement_px", "valid_aperture_fraction",
                        "center_x_px", "center_y_px", "aperture_sum", "background_level",
                        "background_corrected_intensity", "peak_value"
                    } else v) for k, v in item.items()
                }) for item in series_data]
                if [p.frame_index for p in series_candidate] != list(range(len(raw))):
                    raise ValueError("Project I(E) rows are not in source-frame order.")
            # Commit validated project state only after all archive data and results
            # have been reconstructed successfully.
            self.raw_frames, self.frames = raw, working
            self.dark_frames = arrays.get("dark_frames")
            self.flat_frames = arrays.get("flat_frames")
            self.dark_flat_frames = arrays.get("dark_flat_frames")
            self.mask_image = mask_candidate
            self.fit_residual = residual_candidate
            source = metadata.get("source_path")
            self.image_path = Path(source) if source else Path(path)
            self.selected = selected_candidate
            self.fit_result = fit_candidate
            self.fit_frame_index = fit_frame_candidate
            self.fit_radius_used = fit_radius_candidate
            self.series_result = series_candidate
            for name, widget in (("energy_start", self.energy_start), ("energy_step", self.energy_step),
                                 ("fit_radius", self.fit_radius), ("aperture_radius", self.aperture_radius),
                                 ("search_radius", self.search_radius), ("max_displacement", self.max_displacement),
                                 ("background_inner", self.background_inner),
                                 ("background_outer", self.background_outer)):
                if name in settings:
                    widget.blockSignals(True)
                    widget.setValue(settings[name])
                    widget.blockSignals(False)
            self._update_background_radii(self.aperture_radius.value())
            self.energy_confirm.blockSignals(True)
            self.energy_confirm.setChecked(bool(metadata.get("energy_axis_confirmed", False)))
            self.energy_confirm.blockSignals(False)
            mode = metadata.get("calibration_mode", "average")
            self.calibration_mode.blockSignals(True)
            mode_index = self.calibration_mode.findData(mode)
            self.calibration_mode.setCurrentIndex(mode_index if mode_index >= 0 else 0)
            self.calibration_mode.blockSignals(False)
            self.corrections_dirty = bool(metadata.get("corrections_dirty", False))
            self.corrections_applied = bool(metadata.get("corrections_applied", False))
            index = index_candidate
            self.frame_slider.blockSignals(True)
            self.frame_slider.setRange(0, len(self.frames)-1)
            self.frame_slider.setValue(index)
            self.frame_slider.blockSignals(False)
            if self.energy_confirm.isChecked():
                energy = self.energy_start.value() + self.energy_step.value() * index
                self.frame_label.setText(f"Frame {index+1} of {len(self.frames)} · {energy:g} eV (confirmed axis)")
            else:
                self.frame_label.setText(f"Frame {index+1} of {len(self.frames)} · energy axis not confirmed")
            self.image_panel.set_image(self.frames[index], auto_range=True, auto_levels=True)
            if self.selected is not None:
                self.image_panel.set_marker(*self.selected)
            self.image_panel.set_track_points(self.series_result or [], index if self.series_result else None)
            if self.fit_residual is not None:
                self.residual_panel.setImage(np.asarray(self.fit_residual).T, autoLevels=True)
            else:
                self.residual_panel.clear()
            if self.fit_result is not None:
                fit = self.fit_result
                self.results.setText(
                    f"Fit valid: {fit.valid} · optimizer converged: {fit.optimizer_success}\n"
                    f"Centre: ({fit.center_x_px:.2f}, {fit.center_y_px:.2f}) px\n"
                    f"Amplitude: {fit.amplitude:.4g} · Background: {fit.background:.4g}\n"
                    f"FWHM: {fit.fwhm_x_px:.3f} × {fit.fwhm_y_px:.3f} px\n"
                    f"R²: {fit.r_squared:.5f} · RMSE: {fit.rmse:.5g}\n{fit.message}"
                )
            else:
                self.results.setText("Project loaded. Select a spot or inspect the saved measurements.")
            self.fit_button.setEnabled(self.selected is not None)
            self.track_button.setEnabled(self.selected is not None and len(self.frames) > 1)
            self.export_fit_button.setEnabled(bool(self.fit_result is not None and self.fit_result.success and self.fit_frame_index == index))
            self.export_series_button.setEnabled(bool(self.series_result))
            has_flags = bool(self.series_result and any(p.quality_flag not in {"ok", "unchecked"} for p in self.series_result))
            self.previous_warning_button.setEnabled(has_flags)
            self.next_warning_button.setEnabled(has_flags)
            self.series_table.setRowCount(0)
            self.curve_plot.clear()
            if self.series_result:
                self.curve_plot.plot([p.energy_ev for p in self.series_result],
                    [p.background_corrected_intensity for p in self.series_result],
                    pen=pg.mkPen("c", width=2), symbol="o", symbolSize=5,
                    symbolBrush=pg.mkBrush("c"), name="Tracked spot")
                self.series_table.setRowCount(len(self.series_result))
                for row, point in enumerate(self.series_result):
                    values = [str(point.frame_index+1), f"{point.energy_ev:.4f}",
                              f"{point.center_x_px:.3f}", f"{point.center_y_px:.3f}",
                              f"{point.background_corrected_intensity:.6g}",
                              f"{point.signal_to_noise_ratio:.3g}", point.quality_flag]
                    for col, value in enumerate(values):
                        self.series_table.setItem(row, col, QTableWidgetItem(value))
                self.series_table.selectRow(index)
            self.curve_plot.addItem(self.curve_cursor)
            self.change_frame(index)
            self.apply_corrections_button.setEnabled(any(x is not None for x in (self.dark_frames, self.flat_frames, self.dark_flat_frames, self.mask_image)))
            self.correction_info.setText(
                f"Dark: {'loaded' if self.dark_frames is not None else 'none'} · "
                f"Flat: {'loaded' if self.flat_frames is not None else 'none'} · "
                f"Flat dark: {'loaded' if self.dark_flat_frames is not None else 'none'} · "
                f"Mask: {'loaded' if self.mask_image is not None else 'none'}"
            )
            self.setWindowTitle(f"LEED Studio 0.11.1 — {Path(path).name}")
            self.workflow_banner.setText("PROJECT OPENED  ·  Review the selected frame and measurement. If this project contains older results, verify the settings and validity messages before exporting.")
            self.session_dirty = False
            self._refresh_data_browser()
            self.statusBar().showMessage(f"Opened project: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Could not open project", str(exc))

    def _export_metadata(self, result_type: str) -> dict:
        source = self.image_path
        source_size = source.stat().st_size if source and source.exists() else None
        source_mtime = (datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat()
                        if source and source.exists() else None)
        return {
            "software": "LEED Studio",
            "software_version": "0.11.1",
            "exported_utc": datetime.now(timezone.utc).isoformat(),
            "result_type": result_type,
            "source_path": str(source) if source else None,
            "source_file_size_bytes": source_size,
            "source_file_modified_utc": source_mtime,
            "stack_shape_frames_height_width": list(self.frames.shape) if self.frames is not None else None,
            "working_dtype": str(self.frames.dtype) if self.frames is not None else None,
            "selected_spot_xy_px": list(self.selected) if self.selected is not None else None,
            "frame_indexing": "zero-based in metadata; CSV frame column is one-based",
            "energy_start_ev": self.energy_start.value(),
            "energy_step_ev": self.energy_step.value(),
            "fit_radius_px": self.fit_radius_used,
            "aperture_radius_px": self.aperture_radius.value(),
            "search_radius_px": self.search_radius.value(),
            "max_displacement_px_per_frame": self.max_displacement.value(),
            "background_inner_radius_px": self.background_inner.value(),
            "background_outer_radius_px": self.background_outer.value(),
            "measurement_method": "local maximum + intensity centroid; circular aperture; median annular background",
            "intensity_units": "detector counts, not calibrated physical intensity",
            "mask_convention": "nonzero=keep; zero=exclude",
            "dark_loaded": self.dark_frames is not None,
            "flat_loaded": self.flat_frames is not None,
            "calibration_mode": str(self.calibration_mode.currentData()),
            "corrections_applied_to_working_stack": self.corrections_applied and not self.corrections_dirty,
            "corrections_pending_not_yet_applied": self.corrections_dirty,
            "energy_axis_confirmed_by_user": self.energy_confirm.isChecked(),
            "dark_for_flat_loaded": self.dark_flat_frames is not None,
            "mask_loaded": self.mask_image is not None,
            "warning": "Exploratory prototype method; not benchmark-validated against ViPErLEED Spot Tracker.",
        }

    def export_fit(self):
        if self.fit_result is None or not self.fit_result.success:
            return
        if self.fit_frame_index != self.frame_slider.value() or self.fit_radius_used != self.fit_radius.value():
            QMessageBox.warning(self, "Fit context changed", "Return to the source frame and original fit radius before exporting this fit.")
            return
        suggested = (self.image_path.stem if self.image_path else "leed_spot") + "_fit.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export fit as CSV", suggested, "CSV files (*.csv)")
        if path:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            try:
                save_fit_csv(path, self.fit_result, self._export_metadata("gaussian_spot_fit"))
                self.statusBar().showMessage(f"Exported fit: {path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export failed", str(exc))

    def export_series(self):
        if not self.series_result:
            return
        suggested = (self.image_path.stem if self.image_path else "leed_spot") + "_iv.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export I(E) as CSV", suggested, "CSV files (*.csv)")
        if path:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            try:
                save_series_csv(path, self.series_result, self._export_metadata("spot_intensity_vs_energy"))
                self.statusBar().showMessage(f"Exported I(E): {path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export failed", str(exc))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LEED Studio")
    app.setOrganizationName("LEED Studio")
    app.setStyle("Fusion")
    icon_path = Path(__file__).resolve().parent / "data" / "leed_studio.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
