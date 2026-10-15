import numpy as np
import pytest

from leed_studio.project_io import save_project, load_project


def test_project_round_trip_preserves_arrays_nan_and_metadata(tmp_path):
    raw = np.arange(2 * 8 * 9, dtype=np.uint16).reshape(2, 8, 9)
    working = raw.astype(float)
    working[:, 0, 0] = np.nan
    path = tmp_path / "test.leedproj"
    save_project(path, {"raw_frames": raw, "frames": working, "mask": None},
                 {"frame_index": 1, "selected": [2.5, 3.5], "quality": float("nan")})
    arrays, metadata = load_project(path)
    assert arrays["raw_frames"].dtype == np.uint16
    assert np.array_equal(arrays["raw_frames"], raw)
    assert np.array_equal(arrays["frames"], working, equal_nan=True)
    assert metadata["quality"] is None
    assert metadata["frame_index"] == 1


def test_project_rejects_non_project_zip(tmp_path):
    path = tmp_path / "bad.leedproj"
    path.write_text("not a zip")
    with pytest.raises(ValueError, match="valid LEED Studio"):
        load_project(path)


def test_project_rejects_wrong_format(tmp_path):
    import json, zipfile
    path = tmp_path / "wrong.leedproj"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", json.dumps({"format": "other", "version": 1}))
        z.writestr("arrays.npz", b"invalid")
    with pytest.raises(ValueError, match="not a LEED Studio project"):
        load_project(path)


def test_project_rejects_unexpected_archive_members(tmp_path):
    import json, zipfile
    path = tmp_path / "extra.leedproj"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", json.dumps({"format": "leed-studio-project", "version": 1, "arrays": {}, "metadata": {}}))
        z.writestr("arrays.npz", b"invalid")
        z.writestr("unexpected.txt", "extra")
    with pytest.raises(ValueError, match="exactly manifest.json and arrays.npz"):
        load_project(path)


def test_project_save_rejects_complex_arrays(tmp_path):
    path = tmp_path / "complex.leedproj"
    with pytest.raises(ValueError, match="real numeric or boolean"):
        save_project(path, {"raw_frames": np.ones((1, 4, 4), dtype=np.complex64)}, {})


def test_project_save_requires_dictionary_metadata(tmp_path):
    path = tmp_path / "metadata.leedproj"
    with pytest.raises(ValueError, match="metadata must be a dictionary"):
        save_project(path, {"raw_frames": np.ones((1, 4, 4))}, ["not", "a", "dict"])
