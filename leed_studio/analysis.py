"""Image loading, spot fitting, and energy-series measurements for LEED Studio.

Prototype methods only. Validate all methods against reference data before scientific use.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import math

import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.ndimage import maximum_filter

try:
    import tifffile
except ImportError:  # pragma: no cover
    tifffile = None


@dataclass
class SpotFit:
    center_x_px: float
    center_y_px: float
    amplitude: float
    background: float
    sigma_x_px: float
    sigma_y_px: float
    angle_deg: float
    fwhm_x_px: float
    fwhm_y_px: float
    integrated_gaussian_counts: float
    rmse: float
    roi_radius_px: int
    success: bool
    message: str
    r_squared: float = float("nan")
    n_valid_pixels: int = 0
    center_x_std_px: float = float("nan")
    center_y_std_px: float = float("nan")
    optimizer_success: bool = False
    valid: bool = False
    validation_flags: str = ""
    fit_snr: float = float("nan")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SeriesPoint:
    frame_index: int
    energy_ev: float
    center_x_px: float
    center_y_px: float
    aperture_sum: float
    background_level: float
    background_corrected_intensity: float
    peak_value: float
    aperture_radius_px: int
    tracking_method: str
    signal_to_noise_ratio: float = float("nan")
    displacement_px: float = 0.0
    valid_aperture_fraction: float = 1.0
    quality_flag: str = "unchecked"
    failure_reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _to_grayscale(data: np.ndarray) -> np.ndarray:
    """Convert one RGB/RGBA image to luminance; require a 2D result otherwise."""
    data = np.asarray(data)
    if data.ndim == 3 and data.shape[-1] in (3, 4):
        # Explicit luminance conversion for visualization/analysis. Detector data
        # with meaningful independent colour channels should be split beforehand.
        rgb = data[..., :3].astype(np.float64, copy=False)
        data = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    if data.ndim != 2:
        raise ValueError(f"Expected a 2D image, got shape {data.shape}")
    data = np.asarray(data)
    if not np.isfinite(data).all():
        raise ValueError("Image contains NaN or infinite values.")
    return data


def _working_dtype(source: np.ndarray):
    """Use float32 for common <=16-bit detector data, float64 for wider data."""
    dtype = np.asarray(source).dtype
    if dtype.kind in "iu" and dtype.itemsize <= 2:
        return np.float32
    if dtype.kind == "f" and dtype.itemsize <= 4:
        return np.float32
    return np.float64


def load_image_stack(path: str | Path) -> np.ndarray:
    """Load an image/TIFF series as (frames, height, width), checking TIFF axes.

    Leading time/z/page-like dimensions are flattened into frames. RGB(A) data
    with an explicit sample axis is converted to luminance. Ambiguous channel
    axes are rejected rather than silently treated as time frames.
    """
    path = Path(path)
    if path.suffix.lower() in {".tif", ".tiff"} and tifffile is not None:
        with tifffile.TiffFile(path) as tif:
            if not tif.series:
                raise ValueError("TIFF contains no readable image series.")
            series = tif.series[0]
            data = series.asarray()
            axes = getattr(series, "axes", "") or ""
        if data.ndim == 2:
            frames = data[np.newaxis, :, :]
        elif axes.endswith("YXS") and data.shape[-1] in (3, 4):
            if data.ndim == 3:
                frames = _to_grayscale(data)[np.newaxis, :, :]
            else:
                leading_shape = data.shape[:-3]
                reshaped = data.reshape((-1,) + data.shape[-3:])
                frames = np.stack([_to_grayscale(frame) for frame in reshaped])
        elif axes.endswith("YX"):
            unsupported = [axis for axis, size in zip(axes[:-2], data.shape[:-2])
                           if axis not in "ITZQ" and size > 1]
            if unsupported:
                raise ValueError(
                    f"TIFF series has ambiguous non-spatial axes {unsupported} ({axes}); "
                    "select/export the intended channel as a separate grayscale stack."
                )
            frames = data.reshape((-1,) + data.shape[-2:])
        elif data.ndim == 3 and data.shape[-1] in (3, 4):
            # Fallback for TIFF writers that omit useful axis metadata.
            frames = _to_grayscale(data)[np.newaxis, :, :]
        else:
            raise ValueError(
                f"Unsupported TIFF dimensions/axes: shape={data.shape}, axes={axes or 'unknown'}. "
                "Export a grayscale image stack with explicit spatial Y/X axes."
            )
        dtype = _working_dtype(data)
    else:
        with Image.open(path) as im:
            data = np.asarray(im)
        if data.ndim == 3 and data.shape[-1] in (3, 4):
            frames = _to_grayscale(data)[np.newaxis, :, :]
        elif data.ndim == 2:
            frames = data[np.newaxis, :, :]
        else:
            raise ValueError(f"Unsupported image dimensions {data.shape}.")
        dtype = _working_dtype(data)
    frames = np.asarray(frames, dtype=dtype)
    if frames.ndim != 3:
        raise ValueError(f"Expected frames × height × width, got {frames.shape}")
    if not np.isfinite(frames).all():
        raise ValueError("Image stack contains NaN or infinite values.")
    if min(frames.shape) < 1:
        raise ValueError("Image stack has an empty dimension.")
    return frames


def load_image(path: str | Path) -> np.ndarray:
    """Load a single image; reject multipage stacks to avoid silent data loss."""
    frames = load_image_stack(path)
    if len(frames) != 1:
        raise ValueError(f"File contains {len(frames)} frames; use load_image_stack().")
    return frames[0]



def correct_detector_frames(frames: np.ndarray, dark_frame: np.ndarray | None = None,
                            flat_field: np.ndarray | None = None,
                            calibration_mode: str = "average") -> np.ndarray:
    """Compatibility wrapper around the unified correction implementation."""
    try:
        return correct_image_stack(
            frames, dark=dark_frame, flat=flat_field,
            dark_for_flat=dark_frame if flat_field is not None else None,
            calibration_mode=calibration_mode,
        )
    except ValueError as exc:
        if "must be positive" in str(exc):
            raise ValueError(
                "Flat field must be strictly greater than the dark frame at every retained pixel."
            ) from exc
        raise


def correct_image_stack(raw: np.ndarray, dark: np.ndarray | None = None,
                        flat: np.ndarray | None = None,
                        dark_for_flat: np.ndarray | None = None,
                        mask: np.ndarray | None = None,
                        calibration_mode: str = "average") -> np.ndarray:
    """Apply dark subtraction, normalized flat-field correction, and a keep-mask.

    Nonzero mask pixels are retained. Invalid flat denominators are permitted only
    outside the retained mask; retained invalid pixels are rejected rather than
    silently repaired. Correction arrays with multiple frames are averaged unless
    they exactly match the data-stack length, in which case they are frame-wise.
    """
    raw = np.asarray(raw)
    if raw.ndim != 3 or min(raw.shape) < 1 or raw.dtype.kind not in "iuf":
        raise ValueError("raw must have non-empty real numeric shape (frames, height, width)")
    raw = raw.astype(np.float32 if raw.dtype.itemsize <= 4 else np.float64, copy=False)
    if not np.isfinite(raw).all():
        raise ValueError("Raw stack contains NaN or infinite values.")
    n, h, w = raw.shape
    if calibration_mode not in {"average", "framewise"}:
        raise ValueError("calibration_mode must be 'average' or 'framewise'.")

    keep = np.ones((h, w), dtype=bool)
    if mask is not None:
        m = np.asarray(mask)
        if m.dtype.kind not in "biuf":
            raise ValueError("Mask must contain real numeric or boolean values.")
        if m.ndim == 3:
            if m.shape[0] == 1:
                m = m[0]
            else:
                raise ValueError("Mask must be a single 2D image.")
        if m.shape != (h, w):
            raise ValueError("Mask dimensions do not match raw data.")
        if not np.isfinite(m).all():
            raise ValueError("Mask contains non-finite values.")
        keep = np.asarray(m) != 0
        if not keep.any():
            raise ValueError("Mask excludes every pixel; retain at least one pixel.")

    def prepare(value, label):
        if value is None:
            return None
        arr = np.asarray(value)
        if arr.dtype.kind not in "iuf":
            raise ValueError(f"{label} must be a real numeric array.")
        arr = arr.astype(np.float64, copy=False)
        if arr.size == 0 or not np.isfinite(arr).all():
            raise ValueError(f"{label} contains no data or non-finite values.")
        if arr.ndim == 2:
            if arr.shape != (h, w):
                raise ValueError(f"{label} image dimensions do not match raw data.")
            return arr[np.newaxis, ...]
        if arr.ndim == 3:
            if arr.shape[1:] != (h, w):
                raise ValueError(f"{label} stack dimensions do not match raw data.")
            if arr.shape[0] == 1:
                return arr
            if calibration_mode == "framewise":
                if arr.shape[0] != n:
                    raise ValueError(
                        f"{label} frame-wise mode requires 1 or {n} calibration frames; got {arr.shape[0]}."
                    )
                return arr
            return np.mean(arr, axis=0, keepdims=True)
        raise ValueError(f"{label} must be a 2D image or 3D stack.")

    d = prepare(dark, "Dark")
    f = prepare(flat, "Flat")
    df = prepare(dark_for_flat, "Dark-for-flat")
    if f is None and df is not None:
        raise ValueError("A dark-for-flat image was supplied without a flat field.")
    corrected = raw.astype(np.float64, copy=True)
    if d is not None:
        corrected -= d
    if f is not None:
        if df is None:
            df = d if d is not None else np.zeros((1, h, w), dtype=float)
        denom = f - df
        # Only pixels retained by the user mask are required to have a valid
        # flat denominator. Invalid excluded pixels are never used downstream.
        retained_denom = denom[..., keep]
        if not np.isfinite(retained_denom).all() or np.any(retained_denom <= 0):
            raise ValueError("Flat minus dark-for-flat must be positive on all retained mask pixels.")
        # Normalize each frame independently. A global median across an energy-varying
        # flat stack introduces artificial frame-to-frame intensity trends even when
        # the raw signal is constant. Static calibration arrays broadcast naturally.
        norms = np.median(retained_denom, axis=1).reshape((-1, 1, 1))
        if not np.isfinite(norms).all() or np.any(norms <= 0):
            raise ValueError("Flat-field normalization must be positive for every calibration frame.")
        safe_denom = np.where((denom > 0) & np.isfinite(denom), denom, 1.0)
        corrected = corrected * norms / safe_denom
    corrected[:, ~keep] = np.nan
    # Return the economical working precision chosen at import for common detector
    # data; calculations above use float64 intermediates for stable normalization.
    return corrected.astype(raw.dtype if raw.dtype == np.float32 else np.float64, copy=False)


def _model(params: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0, y0, amp, bg, sx, sy, theta = params
    ct, st = np.cos(theta), np.sin(theta)
    dx, dy = x - x0, y - y0
    xr = ct * dx + st * dy
    yr = -st * dx + ct * dy
    exponent = -0.5 * ((xr / sx) ** 2 + (yr / sy) ** 2)
    return bg + amp * np.exp(np.clip(exponent, -700, 0))


def fit_spot(image: np.ndarray, center_x: float, center_y: float,
             radius: int = 12) -> tuple[SpotFit, np.ndarray, np.ndarray]:
    """Fit a 2D elliptical Gaussian in a square ROI around a selected point."""
    image = np.asarray(image)
    if image.dtype.kind not in "iuf":
        raise ValueError("Image must contain real numeric pixel values.")
    if image.ndim != 2:
        raise ValueError("Image must be a 2D array.")
    if not np.isfinite(center_x) or not np.isfinite(center_y):
        raise ValueError("Selected spot coordinates must be finite.")
    if isinstance(radius, bool) or not isinstance(radius, (int, np.integer)) or radius < 4:
        raise ValueError("Fitting radius must be an integer of at least 4 pixels.")
    h, w = image.shape
    cx, cy = int(round(center_x)), int(round(center_y))
    x1, x2 = max(0, cx-radius), min(w, cx+radius+1)
    y1, y2 = max(0, cy-radius), min(h, cy+radius+1)
    roi = np.asarray(image[y1:y2, x1:x2], dtype=float)
    if roi.shape[0] < 7 or roi.shape[1] < 7:
        raise ValueError("Selected spot is too close to the image edge for this fit.")
    valid = np.isfinite(roi)
    if int(valid.sum()) < 25:
        raise ValueError("Too few valid pixels in the fit region; check the mask.")
    yy, xx = np.mgrid[y1:y2, x1:x2]
    bg0 = float(np.percentile(roi[valid], 20))
    safe_roi = np.where(valid, roi, -np.inf)
    peak_idx = np.unravel_index(np.argmax(safe_roi), roi.shape)
    px0, py0 = float(xx[peak_idx]), float(yy[peak_idx])
    amp0 = max(float(np.max(roi[valid]) - bg0), np.finfo(float).eps)
    initial = np.array([px0, py0, amp0, bg0, max(radius/3, 1.0),
                        max(radius/3, 1.0), 0.0], dtype=float)
    spread = max(float(np.ptp(roi[valid])), 1.0)
    lower = [x1-0.5, y1-0.5, 0.0, float(np.min(roi[valid])-spread*2),
             0.35, 0.35, -math.pi/2]
    upper = [x2-0.5, y2-0.5, max(amp0*20, 1.0),
             float(np.max(roi[valid])+spread*2), radius*2.0, radius*2.0, math.pi/2]

    result = least_squares(
        lambda p: (_model(p, xx, yy)[valid] - roi[valid]).ravel(),
        initial, bounds=(lower, upper), max_nfev=3000
    )
    fitted = _model(result.x, xx, yy)
    residuals = fitted[valid] - roi[valid]
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    observed = roi[valid]
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((observed - np.mean(observed)) ** 2))
    r_squared = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    # Approximate standard errors from the local least-squares Jacobian. These
    # are diagnostic only: they assume independent, homoscedastic residuals.
    center_x_std = center_y_std = float("nan")
    try:
        dof = int(valid.sum()) - len(result.x)
        if dof > 0 and result.jac.shape[0] > result.jac.shape[1]:
            jtj = result.jac.T @ result.jac
            covariance = np.linalg.pinv(jtj) * (ss_res / dof)
            diag = np.diag(covariance)
            if np.all(np.isfinite(diag[:2])) and np.all(diag[:2] >= 0):
                center_x_std, center_y_std = float(np.sqrt(diag[0])), float(np.sqrt(diag[1]))
    except (ValueError, np.linalg.LinAlgError):
        pass
    x0, y0, amp, bg, sx, sy, theta = result.x
    # Optimizer convergence alone is not scientific validity. A constant/noise-only
    # patch can converge to a zero-amplitude Gaussian with undefined R².
    flags: list[str] = []
    contrast_floor = max(1e-8, 1e-6 * max(float(np.max(np.abs(observed))), 1.0))
    border = np.concatenate((roi[0, :], roi[-1, :], roi[:, 0], roi[:, -1]))
    border = border[np.isfinite(border)]
    border_median = float(np.median(border)) if border.size else float("nan")
    border_noise = (1.4826 * float(np.median(np.abs(border-border_median)))
                    if border.size else float("nan"))
    fit_snr = float(amp / border_noise) if np.isfinite(border_noise) and border_noise > 0 else (
        float("inf") if np.isfinite(amp) and amp > contrast_floor and border_noise == 0 else 0.0
    )
    if not result.success:
        flags.append("optimizer did not converge")
    if not np.all(np.isfinite(result.x)):
        flags.append("non-finite fit parameters")
    if not np.isfinite(r_squared):
        flags.append("R² undefined (no intensity variation)")
    if not np.isfinite(amp) or amp <= contrast_floor:
        flags.append("no significant positive spot amplitude")
    if np.isnan(fit_snr) or fit_snr < 3:
        flags.append("fit amplitude below 3× robust border noise")
    if not np.isfinite(sx) or not np.isfinite(sy) or sx <= 0 or sy <= 0:
        flags.append("invalid spot width")
    # Flag a fit pinned to a width bound: it is usually under-resolved or poorly
    # constrained and should not be treated as an ordinary successful measurement.
    if sx <= 0.36 or sy <= 0.36 or sx >= radius*1.95 or sy >= radius*1.95:
        flags.append("spot width at fit bound")
    fit_valid = bool(result.success and not flags)
    if sx < sy:
        sx, sy = sy, sx
        theta += math.pi / 2
    theta = (theta + math.pi/2) % math.pi - math.pi/2
    fwhm_factor = 2 * math.sqrt(2 * math.log(2))
    fit = SpotFit(
        center_x_px=float(x0), center_y_px=float(y0),
        amplitude=float(amp), background=float(bg),
        sigma_x_px=float(sx), sigma_y_px=float(sy),
        angle_deg=float(np.degrees(theta)),
        fwhm_x_px=float(sx*fwhm_factor),
        fwhm_y_px=float(sy*fwhm_factor),
        integrated_gaussian_counts=float(2*math.pi*amp*sx*sy),
        rmse=rmse, roi_radius_px=int(radius),
        success=bool(result.success), message=str(result.message),
        r_squared=r_squared, n_valid_pixels=int(valid.sum()),
        center_x_std_px=center_x_std, center_y_std_px=center_y_std,
        optimizer_success=bool(result.success), valid=fit_valid,
        validation_flags="; ".join(flags), fit_snr=fit_snr
    )
    # ``success`` is the safe, user-facing status: optimizer convergence AND
    # minimum scientific checks. Preserve optimizer_success separately for debugging.
    fit.success = fit_valid
    if not fit_valid:
        fit.message = f"Numerical optimizer: {result.message}. Validation: {fit.validation_flags}"
    return fit, roi, fitted


def _refine_centroid(frame: np.ndarray, x_peak: float, y_peak: float,
                     centroid_radius: int) -> tuple[float, float]:
    """Subpixel intensity centroid in a small region around a local maximum."""
    h, w = frame.shape
    cx, cy = int(round(x_peak)), int(round(y_peak))
    x1, x2 = max(0, cx-centroid_radius), min(w, cx+centroid_radius+1)
    y1, y2 = max(0, cy-centroid_radius), min(h, cy+centroid_radius+1)
    roi = frame[y1:y2, x1:x2]
    yy, xx = np.mgrid[y1:y2, x1:x2]
    valid = np.isfinite(roi)
    if int(valid.sum()) < 3:
        return float(x_peak), float(y_peak)
    # Remove a robust local floor before calculating a centroid.
    floor = np.percentile(roi[valid], 25)
    weights = np.where(valid, np.clip(roi - floor, 0, None), 0.0)
    total = float(weights.sum())
    if not np.isfinite(total) or total <= np.finfo(float).eps:
        return float(x_peak), float(y_peak)
    return float((weights * xx).sum()/total), float((weights * yy).sum()/total)


def track_spot_series(frames: np.ndarray, initial_x: float, initial_y: float,
                      energies_ev: np.ndarray, aperture_radius: int = 5,
                      search_radius: int = 10, centroid_radius: int = 4,
                      background_inner_px: int | None = None,
                      background_outer_px: int | None = None,
                      start_frame_index: int = 0,
                      max_displacement_px: float | None = None) -> list[SeriesPoint]:
    """Track a spot bidirectionally while preserving per-frame failures.

    Failed frames are returned as rows with NaN measurements and a ``failed:``
    quality flag; a single bad frame no longer destroys the complete I(E) curve.
    The tracker uses a local search ROI and local aperture/annulus arrays to avoid
    allocating several full-image masks for every frame. This remains a baseline
    algorithm, not a validated reproduction of ViPErLEED Spot Tracker.
    """
    source_frames = np.asarray(frames)
    if source_frames.dtype.kind not in "iuf":
        raise ValueError("frames must contain real numeric pixel values.")
    frames = np.asarray(source_frames, dtype=float)
    energies_ev = np.asarray(energies_ev, dtype=float)
    if frames.ndim != 3 or min(frames.shape) < 1:
        raise ValueError("frames must have non-empty shape (n_frames, height, width)")
    if energies_ev.ndim != 1:
        raise ValueError("Energy values must be a one-dimensional array.")
    if len(frames) != len(energies_ev):
        raise ValueError("Number of energy values must equal number of frames")
    if np.isinf(frames).any():
        raise ValueError("Image stack contains infinite pixel values; use NaN only for explicitly masked pixels.")
    if not np.isfinite(energies_ev).all():
        raise ValueError("Energy values must contain only finite values.")
    if not np.isfinite(frames).any():
        raise ValueError("The image stack contains no valid pixels.")
    if not 0 <= start_frame_index < len(frames):
        raise ValueError("start_frame_index is outside the image stack.")
    if aperture_radius < 1 or search_radius < 1 or centroid_radius < 1:
        raise ValueError("Aperture, search, and centroid radii must be positive.")
    if max_displacement_px is None:
        max_displacement_px = max(2.5, search_radius * 0.30)
    if not np.isfinite(max_displacement_px) or max_displacement_px <= 0:
        raise ValueError("max_displacement_px must be a finite positive value.")
    inner = background_inner_px if background_inner_px is not None else aperture_radius + 2
    outer = background_outer_px if background_outer_px is not None else aperture_radius + 5
    if inner <= aperture_radius or outer <= inner:
        raise ValueError("Background annulus must be outside the aperture.")
    if not np.isfinite(initial_x) or not np.isfinite(initial_y):
        raise ValueError("Initial spot coordinates must be finite.")
    n, h, w = frames.shape
    if not (0 <= initial_x < w and 0 <= initial_y < h):
        raise ValueError("Initial spot coordinates are outside the image.")

    missing = float("nan")
    measured: dict[int, SeriesPoint] = {}

    def failed_point(idx: int, reason: str) -> SeriesPoint:
        return SeriesPoint(
            frame_index=idx, energy_ev=float(energies_ev[idx]),
            center_x_px=missing, center_y_px=missing, aperture_sum=missing,
            background_level=missing, background_corrected_intensity=missing,
            peak_value=missing, aperture_radius_px=int(aperture_radius),
            tracking_method="local maximum + intensity centroid",
            signal_to_noise_ratio=missing, displacement_px=missing,
            valid_aperture_fraction=0.0, quality_flag="failed: " + reason,
            failure_reason=reason)

    def measure_frame(idx: int, previous_x: float, previous_y: float,
                      enforce_motion_gate: bool = True) -> SeriesPoint:
        frame = frames[idx]
        sx, sy = int(round(previous_x)), int(round(previous_y))
        x1, x2 = max(0, sx-search_radius), min(w, sx+search_radius+1)
        y1, y2 = max(0, sy-search_radius), min(h, sy+search_radius+1)
        search = frame[y1:y2, x1:x2]
        if search.size == 0 or not np.isfinite(search).any():
            raise ValueError("tracking window has no valid pixels")
        safe_search = np.where(np.isfinite(search), search, -np.inf)
        peak_local = np.unravel_index(np.argmax(safe_search), safe_search.shape)
        refine_radius = centroid_radius
        # Once a track is established, prefer the nearest significant local maximum
        # over an arbitrarily brighter neighbouring beam. If no plausible candidate
        # is close enough, the motion gate below marks the frame as failed instead
        # of silently jumping to a different beam.
        if enforce_motion_gate and np.isfinite(safe_search).any():
            finite_values = search[np.isfinite(search)]
            local_floor = float(np.median(finite_values))
            local_mad = float(np.median(np.abs(finite_values-local_floor)))
            strongest = float(np.max(finite_values))
            prominence_floor = local_floor + max(3.0 * 1.4826 * local_mad,
                                                   0.03 * max(strongest-local_floor, 0.0))
            maxima = (safe_search == maximum_filter(safe_search, size=3, mode="nearest"))
            maxima &= np.isfinite(search) & (search >= prominence_floor)
            candidates = np.argwhere(maxima)
            if len(candidates):
                coords = np.column_stack((candidates[:, 1] + x1, candidates[:, 0] + y1))
                distances = np.hypot(coords[:, 0]-previous_x, coords[:, 1]-previous_y)
                eligible = distances <= max_displacement_px
                if eligible.any():
                    # Nearest plausible peak wins; intensity is used only to break
                    # ties, which reduces identity swaps when beams cross or overlap.
                    candidate_indices = np.flatnonzero(eligible)
                    nearest_distance = distances[candidate_indices].min()
                    near = candidate_indices[distances[candidate_indices] <= nearest_distance + 0.75]
                    strengths = search[candidates[near, 0], candidates[near, 1]]
                    chosen = near[int(np.argmax(strengths))]
                    peak_local = tuple(candidates[chosen])
                    other_distances = np.delete(distances, chosen)
                    other_distances = other_distances[other_distances > 0]
                    if other_distances.size:
                        nearest_competitor = float(other_distances.min())
                        # Prevent the centroid window from blending a nearby beam
                        # into the selected spot centre.
                        refine_radius = min(centroid_radius, max(1, int(np.floor(nearest_competitor / 2))))
        peak_x, peak_y = float(x1+peak_local[1]), float(y1+peak_local[0])
        center_x, center_y = _refine_centroid(frame, peak_x, peak_y, refine_radius)
        if not np.isfinite(center_x) or not np.isfinite(center_y):
            raise ValueError("centroid refinement returned a non-finite centre")
        displacement = float(np.hypot(center_x-previous_x, center_y-previous_y))
        if enforce_motion_gate and displacement > max_displacement_px:
            raise ValueError(
                f"candidate moved {displacement:.2f} px, exceeding the configured "
                f"{max_displacement_px:.2f} px/frame motion gate; possible beam switch"
            )

        # Construct only a local bounding box extending to the outer annulus.
        cx, cy = int(round(center_x)), int(round(center_y))
        bx1, bx2 = max(0, cx-outer), min(w, cx+outer+1)
        by1, by2 = max(0, cy-outer), min(h, cy+outer+1)
        if (center_x-outer < 0 or center_y-outer < 0 or
                center_x+outer >= w or center_y+outer >= h):
            raise ValueError("spot/background annulus touches image edge")
        local = frame[by1:by2, bx1:bx2]
        yy, xx = np.mgrid[by1:by2, bx1:bx2]
        r2 = (xx-center_x)**2 + (yy-center_y)**2
        finite = np.isfinite(local)
        aperture_all = r2 <= aperture_radius**2
        annulus_all = (r2 >= inner**2) & (r2 <= outer**2)
        aperture = aperture_all & finite
        annulus = annulus_all & finite
        aperture_total = int(aperture_all.sum())
        aperture_valid = int(aperture.sum())
        annulus_valid = int(annulus.sum())
        if aperture_valid < 3 or annulus_valid < 5:
            raise ValueError("too few valid aperture/background pixels")
        fraction = aperture_valid / max(aperture_total, 1)
        aperture_sum = float(np.sum(local[aperture]))
        annulus_values = local[annulus]
        bg = float(np.median(annulus_values))
        # Do not silently treat a substantially clipped/masked aperture as valid.
        corrected = aperture_sum - bg * aperture_valid if fraction >= 0.8 else missing
        mad = float(np.median(np.abs(annulus_values-bg)))
        robust_noise = 1.4826 * mad
        peak_value = float(np.max(safe_search))
        snr = ((peak_value-bg)/robust_noise if robust_noise > 0
               else (float("inf") if peak_value > bg else 0.0))
        flags = []
        if np.isnan(snr) or snr < 3:
            raise ValueError("spot not distinguishable from local background (SNR < 3)")
        if displacement > max_displacement_px * 0.75:
            flags.append("large jump")
        if fraction < 0.8:
            flags.append("masked aperture; intensity invalid")
        quality = "; ".join(flags) if flags else "ok"
        return SeriesPoint(
            frame_index=idx, energy_ev=float(energies_ev[idx]),
            center_x_px=center_x, center_y_px=center_y,
            aperture_sum=aperture_sum, background_level=bg,
            background_corrected_intensity=float(corrected), peak_value=peak_value,
            aperture_radius_px=int(aperture_radius),
            tracking_method="local maximum + intensity centroid",
            signal_to_noise_ratio=float(snr), displacement_px=displacement,
            valid_aperture_fraction=float(fraction), quality_flag=quality)

    # The selected frame establishes the refined seed used by BOTH directions.
    try:
        seed = measure_frame(start_frame_index, float(initial_x), float(initial_y),
                             enforce_motion_gate=False)
        measured[start_frame_index] = seed
        seed_x, seed_y = seed.center_x_px, seed.center_y_px
    except ValueError as exc:
        measured[start_frame_index] = failed_point(start_frame_index, str(exc))
        seed_x, seed_y = float(initial_x), float(initial_y)

    previous_x, previous_y = seed_x, seed_y
    for idx in range(start_frame_index+1, n):
        try:
            point = measure_frame(idx, previous_x, previous_y)
            measured[idx] = point
            previous_x, previous_y = point.center_x_px, point.center_y_px
        except ValueError as exc:
            measured[idx] = failed_point(idx, str(exc))
            # Keep the last good centre; later frames can recover from transient failures.

    previous_x, previous_y = seed_x, seed_y
    for idx in range(start_frame_index-1, -1, -1):
        try:
            point = measure_frame(idx, previous_x, previous_y)
            measured[idx] = point
            previous_x, previous_y = point.center_x_px, point.center_y_px
        except ValueError as exc:
            measured[idx] = failed_point(idx, str(exc))

    return [measured[i] for i in range(n)]


def measure_spot_series(frames: np.ndarray, center_x: float, center_y: float,
                        energies_ev: np.ndarray, radius: int = 5,
                        background_inner_px: int | None = None,
                        background_outer_px: int | None = None) -> list[SeriesPoint]:
    """Backward-compatible alias for tracked series measurement."""
    return track_spot_series(
        frames, center_x, center_y, energies_ev, aperture_radius=radius,
        background_inner_px=background_inner_px,
        background_outer_px=background_outer_px
    )


def _write_metadata_sidecar(path: Path, metadata: dict | None) -> None:
    if metadata is None:
        return
    import json
    sidecar = path.with_suffix(path.suffix + ".metadata.json")
    sidecar.write_text(json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def save_fit_csv(path: str | Path, fit: SpotFit, metadata: dict | None = None) -> None:
    path = Path(path)
    if path.suffix.lower() != ".csv":
        path = path.with_suffix(".csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = fit.to_dict()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow(data)
    _write_metadata_sidecar(path, metadata)


def save_series_csv(path: str | Path, points: list[SeriesPoint],
                    metadata: dict | None = None) -> None:
    path = Path(path)
    if path.suffix.lower() != ".csv":
        path = path.with_suffix(".csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not points:
        raise ValueError("No series measurements to export.")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(points[0].to_dict().keys()))
        writer.writeheader()
        writer.writerows(point.to_dict() for point in points)
    _write_metadata_sidecar(path, metadata)

