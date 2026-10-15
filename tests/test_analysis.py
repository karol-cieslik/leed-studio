import numpy as np
import pytest

from leed_studio.analysis import (fit_spot, track_spot_series, load_image_stack,
                                 correct_detector_frames)


def test_fit_recovers_synthetic_gaussian():
    rng = np.random.default_rng(12)
    height, width = 81, 91
    yy, xx = np.mgrid[0:height, 0:width]
    x0, y0, amp, bg, sx, sy = 45.2, 39.4, 800.0, 12.0, 3.1, 4.3
    image = bg + amp * np.exp(-0.5 * (((xx-x0)/sx)**2 + ((yy-y0)/sy)**2))
    image += rng.normal(0, 2, image.shape)
    fit, roi, model = fit_spot(image, x0, y0, radius=12)
    assert fit.success
    assert abs(fit.center_x_px - x0) < 0.2
    assert abs(fit.center_y_px - y0) < 0.2
    assert abs(fit.amplitude - amp) < 20
    assert fit.rmse < 5


def make_drifting_stack():
    rng = np.random.default_rng(41)
    h, w = 80, 90
    yy, xx = np.mgrid[0:h, 0:w]
    amps = [100, 160, 240, 330, 220, 130]
    frames = []
    centers = []
    for i, amp in enumerate(amps):
        x0, y0 = 42 + 0.8*i, 38 + 0.35*i
        centers.append((x0, y0))
        frame = 14 + 0.015*xx + 0.01*yy
        frame = frame + amp*np.exp(-0.5*(((xx-x0)/2.6)**2+((yy-y0)/3.0)**2))
        frame = frame + rng.normal(0, 0.8, frame.shape)
        frames.append(frame)
    return np.stack(frames), amps, centers


def test_tracker_follows_synthetic_drifting_spot():
    frames, amps, centers = make_drifting_stack()
    energies = np.arange(len(frames))*5.0 + 80
    points = track_spot_series(frames, *centers[0], energies,
                               aperture_radius=5, search_radius=5, centroid_radius=4)
    assert len(points) == len(frames)
    assert max(abs(p.center_x_px-c[0]) for p, c in zip(points, centers)) < 1.0
    assert max(abs(p.center_y_px-c[1]) for p, c in zip(points, centers)) < 1.0
    vals = np.array([p.background_corrected_intensity for p in points])
    assert vals.argmax() == 3
    assert points[-1].energy_ev == energies[-1]


def test_tracker_rejects_energy_count_mismatch():
    frames, amps, centers = make_drifting_stack()
    with pytest.raises(ValueError, match="Number of energy"):
        track_spot_series(frames, *centers[0], np.array([1, 2]), aperture_radius=5)


def test_tracker_records_edge_background_failure_without_aborting_series():
    frames = np.ones((3, 30, 30))
    points = track_spot_series(frames, 3, 3, np.array([1, 2, 3]), aperture_radius=4)
    assert len(points) == 3
    assert all(p.quality_flag.startswith("failed:") for p in points)
    assert all(np.isnan(p.background_corrected_intensity) for p in points)


def test_load_multipage_tiff(tmp_path):
    tifffile = pytest.importorskip("tifffile")
    arr = np.zeros((3, 20, 25), dtype=np.uint16)
    arr[0, 10, 10] = 100
    arr[1, 10, 10] = 200
    arr[2, 10, 10] = 300
    path = tmp_path / "stack.tif"
    tifffile.imwrite(path, arr, photometric="minisblack")
    loaded = load_image_stack(path)
    assert loaded.shape == (3, 20, 25)
    assert loaded[:, 10, 10].tolist() == [100, 200, 300]



def test_tracker_can_start_from_middle_frame_and_tracks_both_directions():
    frames, amps, centers = make_drifting_stack()
    energies = np.arange(len(frames))*5.0 + 80
    start = 3
    points = track_spot_series(
        frames, *centers[start], energies, aperture_radius=5,
        search_radius=5, centroid_radius=4, start_frame_index=start
    )
    assert [p.frame_index for p in points] == list(range(len(frames)))
    assert max(abs(p.center_x_px-c[0]) for p, c in zip(points, centers)) < 1.0
    assert max(abs(p.center_y_px-c[1]) for p, c in zip(points, centers)) < 1.0



def test_dark_and_flat_field_correction():
    h, w = 30, 32
    dark = np.full((h, w), 10.0)
    flat = np.linspace(100, 200, h*w).reshape(h, w)
    true_signal = np.full((2, h, w), 50.0)
    raw = dark[None, :, :] + true_signal * ((flat-dark) / np.median(flat-dark))[None, :, :]
    corrected = correct_detector_frames(raw, dark, flat)
    assert corrected.shape == raw.shape
    assert np.allclose(corrected, 50.0, atol=1e-10)


def test_flat_field_rejects_nonpositive_after_dark():
    frames = np.ones((1, 10, 10))*10
    dark = np.ones((10, 10))*5
    flat = np.ones((10, 10))*4
    with pytest.raises(ValueError, match="strictly greater"):
        correct_detector_frames(frames, dark, flat)



def test_dark_flat_correction_preserves_scale_for_uniform_flat():
    from leed_studio.analysis import correct_image_stack
    raw = np.full((2, 8, 8), 30.0)
    dark = np.full((8, 8), 10.0)
    flat = np.full((8, 8), 5.0)
    dark_flat = np.full((8, 8), 1.0)
    corrected = correct_image_stack(raw, dark=dark, flat=flat, dark_for_flat=dark_flat)
    # A spatially uniform flat should not change the scale after normalization.
    assert np.allclose(corrected, 20.0)


def test_dark_flat_rejects_nonpositive_denominator():
    from leed_studio.analysis import correct_image_stack
    raw = np.ones((1, 8, 8))
    flat = np.ones((8, 8))
    with pytest.raises(ValueError, match="must be positive"):
        correct_image_stack(raw, flat=flat, dark_for_flat=np.ones((8, 8)))


def test_mask_excludes_pixels_from_analysis():
    from leed_studio.analysis import correct_image_stack
    raw = np.full((1, 8, 8), 9.0)
    mask = np.ones((8, 8), dtype=np.uint8)
    mask[:4, :] = 0
    corrected = correct_image_stack(raw, mask=mask)
    assert np.isnan(corrected[:, :4, :]).all()
    assert np.all(corrected[:, 4:, :] == 9)



def test_flat_field_correction_preserves_constant_signal_scale():
    from leed_studio.analysis import correct_image_stack
    h, w = 12, 14
    dark = np.full((h, w), 10.0)
    flat = np.linspace(50, 150, h*w).reshape(h, w)
    flat_dark = np.full((h, w), 5.0)
    # A uniform 40-count signal modulated by the flat's sensitivity.
    response = flat - flat_dark
    raw = dark[None, :, :] + 40.0 * response[None, :, :] / np.median(response)
    corrected = correct_image_stack(raw, dark=dark, flat=flat, dark_for_flat=flat_dark)
    assert np.allclose(corrected, 40.0, atol=1e-10)



def test_masked_pixels_are_excluded_from_spot_tracking():
    from leed_studio.analysis import correct_image_stack, track_spot_series
    h, w = 50, 50
    yy, xx = np.mgrid[:h, :w]
    spot = 20 + 120*np.exp(-0.5*(((xx-25)/2.5)**2 + ((yy-25)/2.5)**2))
    frames = np.stack([spot, spot*1.5])
    mask = np.ones((h, w), dtype=np.uint8)
    mask[:10, :] = 0
    corrected = correct_image_stack(frames, mask=mask)
    assert np.isnan(corrected[:, :10, :]).all()
    points = track_spot_series(
        corrected, 25, 25, np.array([40.0, 41.0]),
        aperture_radius=4, search_radius=4
    )
    assert len(points) == 2
    assert all(abs(p.center_x_px-25) < 0.3 for p in points)


def test_tracker_ignores_nan_masked_pixels_in_search_window():
    from leed_studio.analysis import track_spot_series
    frames, _, centers = make_drifting_stack()
    # Mask the brightest pixel in one frame. The tracker must still choose a finite pixel.
    frames = frames.astype(float)
    frames[2, 38:44, 42:48] = np.nan
    energies = np.arange(len(frames), dtype=float)
    points = track_spot_series(frames, *centers[0], energies,
                               aperture_radius=3, search_radius=5, centroid_radius=2)
    assert all(np.isfinite(p.center_x_px) and np.isfinite(p.center_y_px) for p in points)
    assert "masked aperture" in points[2].quality_flag or points[2].quality_flag in {"ok", "low SNR"}


def test_fit_reports_diagnostics():
    yy, xx = np.mgrid[:61, :61]
    image = 4 + 200*np.exp(-0.5*(((xx-30.2)/2.3)**2 + ((yy-28.7)/3.1)**2))
    fit, _, _ = fit_spot(image, 30, 29, radius=10)
    assert fit.success
    assert fit.r_squared > 0.99
    assert fit.n_valid_pixels > 100
    assert np.isfinite(fit.center_x_std_px)


def test_tracker_rejects_initial_point_outside_image():
    frames, _, _ = make_drifting_stack()
    with pytest.raises(ValueError, match="outside the image"):
        track_spot_series(frames, -1, 12, np.arange(len(frames)), aperture_radius=3)


def test_correction_rejects_nonfinite_calibration():
    from leed_studio.analysis import correct_image_stack
    raw = np.ones((1, 10, 10))
    dark = np.ones((10, 10))
    dark[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        correct_image_stack(raw, dark=dark)


def test_dark_for_flat_requires_flat_field():
    from leed_studio.analysis import correct_image_stack
    raw = np.ones((1, 10, 10))
    with pytest.raises(ValueError, match="without a flat field"):
        correct_image_stack(raw, dark_for_flat=np.ones((10, 10)))


def test_fit_rejects_nonfinite_selected_coordinate():
    image = np.ones((30, 30))
    with pytest.raises(ValueError, match="coordinates must be finite"):
        fit_spot(image, float("nan"), 10, radius=5)


def test_tracker_recovers_after_one_masked_frame():
    frames, _, centers = make_drifting_stack()
    frames = frames.copy()
    frames[2, :, :] = np.nan
    energies = np.arange(len(frames), dtype=float)
    points = track_spot_series(frames, *centers[0], energies, aperture_radius=5,
                               search_radius=5, centroid_radius=4)
    assert len(points) == len(frames)
    assert points[2].quality_flag.startswith("failed:")
    assert np.isnan(points[2].background_corrected_intensity)
    assert points[3].quality_flag != "failed: tracking window has no valid pixels"
    assert np.isfinite(points[3].center_x_px)


def test_masked_aperture_marks_intensity_invalid():
    from leed_studio.analysis import correct_image_stack
    h, w = 60, 60
    yy, xx = np.mgrid[:h, :w]
    frame = 10 + 100*np.exp(-0.5*(((xx-30)/2.5)**2 + ((yy-30)/2.5)**2))
    mask = np.ones((h, w), dtype=np.uint8)
    mask[27:34, 30:34] = 0
    corrected = correct_image_stack(frame[None, ...], mask=mask)
    point = track_spot_series(corrected, 30, 30, np.array([50.0]), aperture_radius=5,
                              search_radius=4, centroid_radius=3)[0]
    assert "masked aperture" in point.quality_flag
    assert np.isnan(point.background_corrected_intensity)


def test_flat_field_invalid_pixels_are_allowed_only_when_masked_out():
    from leed_studio.analysis import correct_image_stack
    raw = np.full((1, 8, 8), 20.0)
    flat = np.full((8, 8), 10.0)
    flat[0, 0] = 0.0
    mask = np.ones((8, 8), dtype=np.uint8)
    mask[0, 0] = 0
    corrected = correct_image_stack(raw, flat=flat, mask=mask)
    assert np.isnan(corrected[0, 0, 0])
    assert np.allclose(corrected[0, 1:, :], 20.0)


def test_backward_tracking_uses_refined_selected_frame_seed():
    h, w = 60, 70
    yy, xx = np.mgrid[:h, :w]
    frames = []
    centers = [(22.0, 30.0), (23.0, 30.0), (24.0, 30.0)]
    for i, (cx, cy) in enumerate(centers):
        frame = np.full((h, w), 5.0)
        frame += 100*np.exp(-0.5*(((xx-cx)/2.0)**2 + ((yy-cy)/2.0)**2))
        if i == 1:
            # This bright distractor lies within the original click's search window,
            # but outside the refined selected-frame centre's search window.
            frame += 350*np.exp(-0.5*(((xx-17.0)/1.0)**2 + ((yy-cy)/1.0)**2))
        frames.append(frame)
    points = track_spot_series(np.stack(frames), 22.0, 30.0, np.array([50., 51., 52.]),
                               aperture_radius=3, search_radius=5, centroid_radius=2,
                               start_frame_index=2)
    assert abs(points[1].center_x_px - 23.0) < 0.8
    assert abs(points[0].center_x_px - 22.0) < 0.8


def test_tiff_grayscale_image_with_three_pixel_width_is_not_rgb(tmp_path):
    tifffile = pytest.importorskip("tifffile")
    arr = np.arange(30, dtype=np.uint16).reshape(10, 3)
    path = tmp_path / "narrow.tif"
    tifffile.imwrite(path, arr, photometric="minisblack", metadata={"axes": "YX"})
    loaded = load_image_stack(path)
    assert loaded.shape == (1, 10, 3)
    assert np.array_equal(loaded[0], arr.astype(np.float32))


def test_tiff_ambiguous_channel_axis_is_rejected(tmp_path):
    tifffile = pytest.importorskip("tifffile")
    arr = np.zeros((3, 10, 12), dtype=np.uint16)
    path = tmp_path / "channels.tif"
    tifffile.imwrite(path, arr, photometric="minisblack", metadata={"axes": "CYX"})
    with pytest.raises(ValueError, match="ambiguous non-spatial axes"):
        load_image_stack(path)


def test_series_export_writes_provenance_sidecar_and_csv_extension(tmp_path):
    import json
    from leed_studio.analysis import save_series_csv
    frames, _, centers = make_drifting_stack()
    points = track_spot_series(frames, *centers[0], np.arange(len(frames), dtype=float),
                               aperture_radius=5, search_radius=5)
    requested = tmp_path / "curve"
    save_series_csv(requested, points, {"software_version": "0.9.0", "source_path": "stack.tif"})
    csv_path = tmp_path / "curve.csv"
    sidecar = tmp_path / "curve.csv.metadata.json"
    assert csv_path.exists() and sidecar.exists()
    assert "quality_flag" in csv_path.read_text(encoding="utf-8").splitlines()[0]
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    assert metadata["software_version"] == "0.9.0"


def test_constant_background_is_not_accepted_as_a_valid_gaussian_fit():
    image = np.full((41, 41), 100.0)
    fit, _, _ = fit_spot(image, 20, 20, radius=10)
    # Numerical optimization may terminate normally, but no spot exists.
    assert not fit.success
    assert not fit.valid
    assert fit.validation_flags
    assert "amplitude" in fit.validation_flags or "R² undefined" in fit.validation_flags


def test_framewise_flat_normalization_does_not_invent_energy_trend():
    from leed_studio.analysis import correct_image_stack
    raw = np.full((2, 12, 12), 100.0)
    flat = np.stack([np.full((12, 12), 10.0), np.full((12, 12), 20.0)])
    corrected = correct_image_stack(raw, flat=flat, calibration_mode="framewise")
    assert np.allclose(corrected, 100.0)
    assert np.allclose(corrected[0], corrected[1])


def test_default_calibration_mode_averages_stack_instead_of_guessing_synchronization():
    from leed_studio.analysis import correct_image_stack
    raw = np.full((2, 12, 12), 100.0)
    flat = np.stack([np.full((12, 12), 10.0), np.full((12, 12), 20.0)])
    corrected = correct_image_stack(raw, flat=flat)
    assert np.allclose(corrected, 100.0)


def test_framewise_calibration_requires_explicitly_matching_frame_count():
    from leed_studio.analysis import correct_image_stack
    raw = np.ones((3, 10, 10))
    flat = np.ones((2, 10, 10)) * 10
    with pytest.raises(ValueError, match="requires 1 or 3 calibration frames"):
        correct_image_stack(raw, flat=flat, calibration_mode="framewise")


def test_tracker_prefers_nearest_significant_beam_over_brighter_neighbour():
    h, w = 50, 70
    yy, xx = np.mgrid[:h, :w]
    frames = []
    centers = []
    for i in range(3):
        cx = 20.0 + i
        centers.append(cx)
        frame = np.full((h, w), 10.0)
        frame += 100*np.exp(-0.5*(((xx-cx)/1.4)**2 + ((yy-25)/1.6)**2))
        if i >= 1:
            frame += 500*np.exp(-0.5*(((xx-27)/1.2)**2 + ((yy-25)/1.2)**2))
        frames.append(frame)
    points = track_spot_series(np.stack(frames), 20, 25, np.arange(3, dtype=float),
                               aperture_radius=3, search_radius=8, centroid_radius=2,
                               background_inner_px=5, background_outer_px=9,
                               max_displacement_px=2.5)
    for i, point in enumerate(points):
        assert not point.quality_flag.startswith("failed:"), point.quality_flag
        assert abs(point.center_x_px-centers[i]) < 0.8


def test_uniform_image_is_not_reported_as_successful_spot_measurement():
    frames = np.full((3, 40, 40), 25.0)
    points = track_spot_series(frames, 20, 20, np.array([30.0, 30.5, 31.0]),
                               aperture_radius=3, search_radius=5, centroid_radius=2,
                               background_inner_px=5, background_outer_px=8)
    assert all(point.quality_flag.startswith("failed:") for point in points)
    assert all(np.isnan(point.background_corrected_intensity) for point in points)


def test_fit_rejects_noise_only_patch():
    rng = np.random.default_rng(7)
    image = 100.0 + rng.normal(0, 2.0, (41, 41))
    fit, _, _ = fit_spot(image, 20, 20, radius=10)
    assert not fit.success
    assert "robust border noise" in fit.validation_flags or "spot width at fit bound" in fit.validation_flags


def test_tracker_requires_one_dimensional_energy_axis():
    frames, _, centers = make_drifting_stack()
    with pytest.raises(ValueError, match="one-dimensional"):
        track_spot_series(frames, *centers[0], np.arange(len(frames)).reshape(-1, 1))


def test_correction_rejects_complex_raw_pixels():
    from leed_studio.analysis import correct_image_stack
    raw = np.ones((1, 8, 8), dtype=np.complex64)
    with pytest.raises(ValueError, match="real numeric"):
        correct_image_stack(raw)
