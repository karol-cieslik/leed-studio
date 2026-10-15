#!/usr/bin/env python3
"""Compare LEED Studio spot tracking with published TU Wien Fe2O3 reference coordinates.

This is a reproducible *coordinate benchmark*, not an exact reproduction of ViPErLEED
intensity extraction. The current LEED Studio algorithm does not implement the full
ViPErLEED dark/flat polynomial correction, beam-tail subtraction, variable aperture,
or instrument-current normalization.

Expected public files from DOI 10.48436/hgg42-xss85:
  - one IV_videos/*.zip archive containing a TIFF stack or a sequence of image frames
  - matching Spot_Tracker-extraction/*_x.csv and *_y.csv files

Example (after extracting the public data archive):
  python tools/benchmark_tuwien_fe2o3.py \
    --frames-zip "IV_videos/2022-06-09_03-45-22 - Ti_Fe2O3(1-102)#606 - 1x1 - x=23.35.zip" \
    --reference-x "Spot_Tracker-extraction/2022-06-09_03-45-22-Ti_Fe2O3(1-102)#606-1x1-x=23.35_x.csv" \
    --reference-y "Spot_Tracker-extraction/2022-06-09_03-45-22-Ti_Fe2O3(1-102)#606-1x1-x=23.35_y.csv" \
    --beam-row 0 --output benchmark_beam0

CSV beam rows are zero-based after the script removes a recognizable energy header.
The frame order is natural-sorted by archive member path. Inspect the report and ensure
that this matches the acquisition/reference frame order before interpreting metrics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

# Allow direct execution from a source checkout without installing the package.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from leed_studio.analysis import track_spot_series, save_series_csv

DATASET_DOI = "10.48436/hgg42-xss85"
IMAGE_SUFFIXES = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}


def natural_key(value: str):
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)]


def read_numeric_matrix(path: Path) -> np.ndarray:
    rows = []
    max_width = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        for row in csv.reader(handle):
            vals = []
            for cell in row:
                try:
                    value = float(cell.strip())
                    vals.append(value if math.isfinite(value) else np.nan)
                except (ValueError, AttributeError):
                    vals.append(np.nan)
            if sum(np.isfinite(vals)) >= 2:
                rows.append(vals)
                max_width = max(max_width, len(vals))
    if not rows:
        raise ValueError(f"No numeric matrix could be parsed from {path}")
    matrix = np.full((len(rows), max_width), np.nan, dtype=float)
    for i, row in enumerate(rows):
        matrix[i, :len(row)] = row
    matrix = matrix[~np.all(~np.isfinite(matrix), axis=1)]
    matrix = matrix[:, ~np.all(~np.isfinite(matrix), axis=0)]
    return matrix


def orient_reference(matrix: np.ndarray, n_frames: int, energies: np.ndarray) -> np.ndarray:
    """Return shape (beams, frames), removing obvious numeric energy headers/ID columns."""
    a = np.asarray(matrix, dtype=float)
    # Remove a first/last row that is clearly the energy axis, if present.
    for side in ("first", "last"):
        row = a[0, :] if side == "first" else a[-1, :]
        if row.size == n_frames and np.allclose(row, energies, rtol=0, atol=1e-4, equal_nan=False):
            a = a[1:, :] if side == "first" else a[:-1, :]
            break
    # If a beam-row matrix has one extra leading beam-ID column, remove it.
    if a.shape[1] == n_frames + 1:
        a = a[:, 1:]
    elif a.shape[1] == n_frames:
        pass
    elif a.shape[0] == n_frames + 1:
        a = a[1:, :].T
    elif a.shape[0] == n_frames:
        # Some exports orient frames as rows and beams as columns, optionally with
        # a numeric frame index/energy in the first column. Strip that column only
        # when it exactly matches a recognizable frame axis.
        if a.shape[1] > 1:
            first_col = a[:, 0]
            index_axis = np.arange(n_frames, dtype=float)
            if (np.allclose(first_col, index_axis, rtol=0, atol=1e-6, equal_nan=False) or
                    np.allclose(first_col, energies, rtol=0, atol=1e-4, equal_nan=False)):
                a = a[:, 1:]
        a = a.T
    else:
        # Numeric header/index columns/rows can survive parsing; try removing one
        # column or row only when it makes the frame dimension exact.
        if a.shape[1] - 1 == n_frames:
            a = a[:, 1:]
        elif a.shape[0] - 1 == n_frames:
            a = a[1:, :].T
        else:
            raise ValueError(
                f"Reference matrix shape {a.shape} does not contain {n_frames} frames. "
                "Inspect the CSV header and frame count manually."
            )
    if a.shape[1] != n_frames:
        raise ValueError(f"Could not orient reference coordinates to {n_frames} frames: {a.shape}")
    return a


def _decode_image_bytes_cropped(data: bytes, name: str,
                                crop: tuple[int, int, int, int]):
    """Yield each cropped page so multi-page stacks are not duplicated in RAM."""
    x0, y0, x1, y1 = crop
    suffix = Path(name).suffix.lower()
    if suffix in {".tif", ".tiff"}:
        try:
            import tifffile
            with tifffile.TiffFile(io.BytesIO(data)) as tif:
                for page in tif.pages:
                    frame = np.asarray(page.asarray())
                    if frame.ndim == 3 and frame.shape[-1] in (3, 4):
                        rgb = frame[..., :3].astype(np.float32, copy=False)
                        frame = 0.2126*rgb[..., 0] + 0.7152*rgb[..., 1] + 0.0722*rgb[..., 2]
                    if frame.ndim != 2:
                        raise ValueError(f"Unsupported TIFF frame shape {frame.shape} in {name}")
                    cx1, cy1 = min(x1, frame.shape[1]), min(y1, frame.shape[0])
                    if x0 >= cx1 or y0 >= cy1:
                        raise ValueError(f"Reference-derived crop {crop} lies outside frame dimensions {frame.shape}")
                    yield np.asarray(frame[y0:cy1, x0:cx1], dtype=np.float32).copy()
            return
        except ImportError:
            pass
    with Image.open(io.BytesIO(data)) as im:
        for page in ImageSequence.Iterator(im):
            frame = np.asarray(page)
            if frame.ndim == 3 and frame.shape[-1] in (3, 4):
                rgb = frame[..., :3].astype(np.float32, copy=False)
                frame = 0.2126*rgb[..., 0] + 0.7152*rgb[..., 1] + 0.0722*rgb[..., 2]
            if frame.ndim != 2:
                raise ValueError(f"Unsupported image frame shape {frame.shape} in {name}")
            cx1, cy1 = min(x1, frame.shape[1]), min(y1, frame.shape[0])
            if x0 >= cx1 or y0 >= cy1:
                raise ValueError(f"Reference-derived crop {crop} lies outside frame dimensions {frame.shape}")
            yield np.asarray(frame[y0:cy1, x0:cx1], dtype=np.float32).copy()


def load_frame_archive_cropped(path: Path, crop: tuple[int, int, int, int], limit: int | None = None):
    """Read frame images from a ZIP and keep only a common ROI to limit RAM usage."""
    x0, y0, x1, y1 = crop
    with zipfile.ZipFile(path) as archive:
        members = sorted((m for m in archive.infolist()
                          if not m.is_dir() and Path(m.filename).suffix.lower() in IMAGE_SUFFIXES),
                         key=lambda m: natural_key(m.filename))
        if not members:
            raise ValueError(
                "No TIFF/PNG/JPEG/BMP frames were found in the supplied ZIP. "
                "The archive may contain a proprietary video; extract/convert it to an image sequence first."
            )
        frames = []
        frame_names = []
        for member in members:
            raw = archive.read(member)
            decoded = _decode_image_bytes_cropped(raw, member.filename, crop)
            for j, frame in enumerate(decoded):
                if limit is not None and len(frames) >= limit:
                    break
                frames.append(frame)
                frame_names.append(f"{member.filename}#{j}")
            if limit is not None and len(frames) >= limit:
                break
    if not frames:
        raise ValueError("No image frames could be decoded from the archive.")
    shape_set = {frame.shape for frame in frames}
    if len(shape_set) != 1:
        raise ValueError(f"Decoded frames have inconsistent crop shapes: {shape_set}")
    return np.stack(frames).astype(np.float32, copy=False), frame_names


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-zip", type=Path, required=True)
    parser.add_argument("--reference-x", type=Path, required=True)
    parser.add_argument("--reference-y", type=Path, required=True)
    parser.add_argument("--beam-row", type=int, required=True, help="Zero-based reference beam row/column")
    parser.add_argument("--energy-start", type=float, default=30.0)
    parser.add_argument("--energy-step", type=float, default=0.5)
    parser.add_argument("--energy-end", type=float, default=750.0,
                        help="Inclusive last energy; public Fe2O3 sequence ends at 750 eV")
    parser.add_argument("--start-frame", type=int, default=451,
                        help="Default 451 corresponds to 255.5 eV for 30 eV + 0.5 eV/frame")
    parser.add_argument("--aperture-radius", type=int, default=11)
    parser.add_argument("--search-radius", type=int, default=10)
    parser.add_argument("--background-inner", type=int, default=13)
    parser.add_argument("--background-outer", type=int, default=18)
    parser.add_argument("--max-displacement", type=float, default=3.0)
    parser.add_argument("--roi-padding", type=int, default=25)
    parser.add_argument("--frame-limit", type=int, default=None, help="Optional debugging limit")
    parser.add_argument("--output", type=Path, default=Path("tuwien_fe2o3_benchmark"))
    args = parser.parse_args()

    # The full reference trajectory defines only the crop envelope, not the tracker
    # path. The tracker itself receives one seed coordinate and must follow image data.
    x_raw = read_numeric_matrix(args.reference_x)
    y_raw = read_numeric_matrix(args.reference_y)
    # Use the acquisition energy range, rather than the largest CSV dimension, to
    # disambiguate frame axes from numeric beam-ID columns and energy-header rows.
    if args.energy_step <= 0 or args.energy_end < args.energy_start:
        raise ValueError("Energy step must be positive and energy end must not precede energy start.")
    expected_frames_float = (args.energy_end - args.energy_start) / args.energy_step
    if not np.isclose(expected_frames_float, round(expected_frames_float), atol=1e-7):
        raise ValueError("Energy range is not an integer number of energy steps.")
    expected_frames = int(round(expected_frames_float)) + 1
    full_energies = args.energy_start + args.energy_step * np.arange(expected_frames)
    n_frames = min(expected_frames, args.frame_limit) if args.frame_limit is not None else expected_frames
    energies = args.energy_start + args.energy_step * np.arange(n_frames)
    x_matrix = orient_reference(x_raw, expected_frames, full_energies)
    y_matrix = orient_reference(y_raw, expected_frames, full_energies)
    if x_matrix.shape != y_matrix.shape:
        raise ValueError(f"Reference X/Y shapes differ: {x_matrix.shape} vs {y_matrix.shape}")
    if not 0 <= args.beam_row < x_matrix.shape[0]:
        raise ValueError(f"beam-row must be between 0 and {x_matrix.shape[0]-1}")
    ref_x = x_matrix[args.beam_row, :n_frames]
    ref_y = y_matrix[args.beam_row, :n_frames]
    if args.start_frame >= n_frames:
        raise ValueError(f"start-frame {args.start_frame} is outside the selected {n_frames}-frame range")
    valid = np.isfinite(ref_x) & np.isfinite(ref_y)
    if not valid.any() or not valid[args.start_frame]:
        raise ValueError("Selected beam has no finite reference coordinate at the start frame")
    pad = max(args.roi_padding, args.background_outer + args.search_radius + 5)
    x0 = max(0, int(np.floor(np.nanmin(ref_x[valid]))) - pad)
    y0 = max(0, int(np.floor(np.nanmin(ref_y[valid]))) - pad)
    x1 = int(np.ceil(np.nanmax(ref_x[valid]))) + pad + 1
    y1 = int(np.ceil(np.nanmax(ref_y[valid]))) + pad + 1
    crop = (x0, y0, x1, y1)

    frames, frame_names = load_frame_archive_cropped(args.frames_zip, crop, limit=n_frames)
    if len(frames) != n_frames:
        raise ValueError(
            f"Decoded {len(frames)} image frames, but the reference has {n_frames}. "
            "Check the video archive, frame order, and frame limit."
        )
    energies = args.energy_start + args.energy_step*np.arange(len(frames))
    points = track_spot_series(
        frames, ref_x[args.start_frame]-x0, ref_y[args.start_frame]-y0, energies,
        aperture_radius=args.aperture_radius, search_radius=args.search_radius,
        background_inner_px=args.background_inner, background_outer_px=args.background_outer,
        start_frame_index=args.start_frame, max_displacement_px=args.max_displacement,
    )
    predicted_x = np.array([p.center_x_px+x0 for p in points])
    predicted_y = np.array([p.center_y_px+y0 for p in points])
    errors = np.hypot(predicted_x-ref_x[:len(points)], predicted_y-ref_y[:len(points)])
    compare = valid[:len(points)] & np.isfinite(errors)
    finite_errors = errors[compare]
    failed = np.array([p.quality_flag.startswith("failed:") for p in points])
    report = {
        "dataset": "ViPErLEED Supporting Information — LEED-I(V) Fe2O3(1-102)-(1x1)",
        "dataset_doi": DATASET_DOI,
        "source_archive": str(args.frames_zip),
        "source_archive_sha256": sha256_file(args.frames_zip),
        "reference_x": str(args.reference_x),
        "reference_y": str(args.reference_y),
        "beam_row_zero_based": args.beam_row,
        "frame_count": len(frames),
        "frame_order": "natural-sorted ZIP member paths; verify against dataset README/log",
        "crop_xyxy": list(crop),
        "energy_start_ev": args.energy_start,
        "energy_step_ev": args.energy_step,
        "energy_end_ev": float(energies[-1]),
        "start_frame_index": args.start_frame,
        "start_energy_ev": float(energies[args.start_frame]),
        "tracking_parameters": {
            "aperture_radius_px": args.aperture_radius,
            "search_radius_px": args.search_radius,
            "background_inner_px": args.background_inner,
            "background_outer_px": args.background_outer,
            "max_displacement_px_per_frame": args.max_displacement,
        },
        "valid_reference_points": int(valid.sum()),
        "compared_points": int(compare.sum()),
        "failed_tracking_frames": int(failed.sum()),
        "coordinate_error_px": {
            "median": float(np.median(finite_errors)) if finite_errors.size else None,
            "rmse": float(np.sqrt(np.mean(finite_errors**2))) if finite_errors.size else None,
            "p95": float(np.percentile(finite_errors, 95)) if finite_errors.size else None,
            "fraction_within_1px": float(np.mean(finite_errors <= 1.0)) if finite_errors.size else None,
        },
        "limitations": [
            "Coordinate-only comparison; LEED Studio has not reproduced the ViPErLEED processing chain.",
            "No numerical I(V) intensity agreement is claimed because the aperture/background definitions differ.",
            "Verify the frame order and coordinate matrix orientation against the published log before interpreting metrics.",
            "Reference positions define the crop envelope and the one seed coordinate, but do not guide the per-frame tracker.",
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    save_series_csv(args.output / "leed_studio_tracking.csv", points, {
        "dataset_doi": DATASET_DOI, "benchmark_type": "coordinate comparison",
        "beam_row_zero_based": args.beam_row, "crop_xyxy": list(crop),
        "warning": "Not an exact ViPErLEED Spot Tracker reproduction",
    })
    with (args.output / "benchmark_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    with (args.output / "coordinate_errors.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame_index_zero_based", "energy_eV", "reference_x_px", "reference_y_px",
                         "leed_studio_x_px", "leed_studio_y_px", "error_px", "quality_flag"])
        for i, point in enumerate(points):
            writer.writerow([i, point.energy_ev, ref_x[i], ref_y[i], predicted_x[i], predicted_y[i],
                             errors[i] if np.isfinite(errors[i]) else "", point.quality_flag])
    print(json.dumps(report, indent=2))
    print(f"\nWrote benchmark outputs to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
