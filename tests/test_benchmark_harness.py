import csv
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest


def test_public_dataset_benchmark_harness_on_controlled_fixture(tmp_path):
    tifffile = pytest.importorskip("tifffile")
    root = Path(__file__).resolve().parents[1]
    h, w = 50, 60
    yy, xx = np.mgrid[:h, :w]
    frames = []
    xs, ys = [], []
    for i in range(5):
        cx, cy = 20.0 + i * 0.5, 25.0 + i * 0.2
        xs.append(cx)
        ys.append(cy)
        frames.append((10 + 100 * np.exp(-0.5 * (((xx-cx)/2)**2 + ((yy-cy)/2)**2))).astype(np.uint16))
    buffer = io.BytesIO()
    tifffile.imwrite(buffer, np.stack(frames), photometric="minisblack", metadata={"axes": "TYX"})
    archive_path = tmp_path / "frames.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("stack.tif", buffer.getvalue())
    energies = 30 + 0.5 * np.arange(5)
    x_path, y_path = tmp_path / "x.csv", tmp_path / "y.csv"
    for path, values in ((x_path, xs), (y_path, ys)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(energies)
            writer.writerow(values)
    out = tmp_path / "benchmark"
    subprocess.run([
        sys.executable, str(root / "tools" / "benchmark_tuwien_fe2o3.py"),
        "--frames-zip", str(archive_path), "--reference-x", str(x_path),
        "--reference-y", str(y_path), "--beam-row", "0", "--start-frame", "1",
        "--energy-end", "32", "--aperture-radius", "3", "--search-radius", "4",
        "--background-inner", "5", "--background-outer", "8", "--max-displacement", "2",
        "--output", str(out),
    ], check=True, capture_output=True, text=True)
    report = json.loads((out / "benchmark_report.json").read_text(encoding="utf-8"))
    assert report["frame_count"] == 5
    assert report["compared_points"] == 5
    assert report["failed_tracking_frames"] == 0
    assert report["coordinate_error_px"]["rmse"] < 0.1
    assert (out / "coordinate_errors.csv").exists()


def test_reference_matrix_orientation_strips_numeric_frame_index_column():
    from tools.benchmark_tuwien_fe2o3 import orient_reference
    energies = 30 + 0.5 * np.arange(5)
    # Frame rows, first column is a zero-based frame index, remaining columns are beams.
    matrix = np.column_stack((np.arange(5), np.arange(5) + 100, np.arange(5) + 200))
    oriented = orient_reference(matrix, 5, energies)
    assert oriented.shape == (2, 5)
    assert np.array_equal(oriented[0], np.arange(5) + 100)
