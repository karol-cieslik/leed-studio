"""Portable, versioned LEED Studio project-file I/O.

Project files are ZIP containers with a JSON manifest and a NumPy archive. Arrays
are loaded with allow_pickle=False; projects never execute embedded code.
"""
from __future__ import annotations

import json
import math
import zipfile
import tempfile
import shutil
import os
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_FORMAT = "leed-studio-project"
PROJECT_VERSION = 1
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_ARRAY_ARCHIVE_BYTES = 8 * 1024 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_ARRAY_BYTES = 16 * 1024 * 1024 * 1024
ALLOWED_ARRAYS = {"raw_frames", "frames", "dark_frames", "flat_frames", "dark_flat_frames", "mask_image", "fit_residual"}


def _json_safe(value: Any):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"Project metadata contains unsupported value type: {type(value).__name__}")


def save_project(path: str | Path, arrays: dict[str, np.ndarray | None], metadata: dict) -> None:
    """Write a self-contained project, including source and working arrays."""
    clean_arrays: dict[str, np.ndarray] = {}
    for name, array in arrays.items():
        if array is None:
            continue
        if name not in ALLOWED_ARRAYS:
            raise ValueError(f"Unrecognized project array name: {name!r}")
        arr = np.asarray(array)
        if arr.dtype.kind not in "biuf":
            raise ValueError(f"Project array {name!r} must have a real numeric or boolean dtype.")
        if arr.ndim > 4 or any(int(dimension) < 1 for dimension in arr.shape):
            raise ValueError(f"Project array {name!r} has an invalid shape.")
        clean_arrays[name] = arr
    estimated_bytes = sum(int(arr.nbytes) for arr in clean_arrays.values())
    if estimated_bytes > MAX_TOTAL_UNCOMPRESSED_ARRAY_BYTES:
        raise ValueError("Project arrays exceed the safe uncompressed size limit.")
    if not isinstance(metadata, dict):
        raise ValueError("Project metadata must be a dictionary.")

    manifest = {
        "format": PROJECT_FORMAT,
        "version": PROJECT_VERSION,
        "arrays": {name: {"shape": list(arr.shape), "dtype": str(arr.dtype)}
                   for name, arr in clean_arrays.items()},
        "metadata": _json_safe(metadata),
    }
    manifest_bytes = json.dumps(manifest, indent=2, allow_nan=False).encode("utf-8")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write beside the destination and atomically replace only after a complete ZIP
    # has been closed and verified. A failed save will not destroy an earlier project.
    temp_path = None
    try:
        with tempfile.TemporaryDirectory(prefix="leed-studio-project-", dir=path.parent) as temp_dir:
            temp_dir = Path(temp_dir)
            array_path = temp_dir / "arrays.npz"
            np.savez_compressed(array_path, **clean_arrays)
            if array_path.stat().st_size > MAX_ARRAY_ARCHIVE_BYTES:
                raise ValueError("Project array archive is too large to save safely.")
            temp_path = temp_dir / "project.tmp"
            with zipfile.ZipFile(temp_path, "w") as archive:
                archive.writestr("manifest.json", manifest_bytes, compress_type=zipfile.ZIP_DEFLATED)
                archive.write(array_path, arcname="arrays.npz", compress_type=zipfile.ZIP_STORED)
            # Verify the container before the atomic replacement.
            with zipfile.ZipFile(temp_path, "r") as check:
                bad_member = check.testzip()
                if bad_member is not None:
                    raise ValueError(f"Saved project failed ZIP integrity check: {bad_member}")
            os.replace(temp_path, path)
    except Exception:
        raise


def load_project(path: str | Path) -> tuple[dict[str, np.ndarray], dict]:
    """Load and validate a project archive without allowing pickle deserialization."""
    path = Path(path)
    if not zipfile.is_zipfile(path):
        raise ValueError("Not a valid LEED Studio project archive.")
    with zipfile.ZipFile(path, "r") as archive:
        name_list = archive.namelist()
        names = set(name_list)
        if len(name_list) != len(names):
            raise ValueError("Project archive contains duplicate member names.")
        if names != {"manifest.json", "arrays.npz"}:
            raise ValueError("Project must contain exactly manifest.json and arrays.npz.")
        infos = {item.filename: item for item in archive.infolist()}
        if infos["manifest.json"].file_size > MAX_MANIFEST_BYTES:
            raise ValueError("Project manifest is unexpectedly large.")
        if infos["arrays.npz"].file_size > MAX_ARRAY_ARCHIVE_BYTES:
            raise ValueError("Project array archive is too large to load safely.")
        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Project manifest is not valid UTF-8 JSON.") from exc
        if manifest.get("format") != PROJECT_FORMAT:
            raise ValueError("This is not a LEED Studio project.")
        if manifest.get("version") != PROJECT_VERSION:
            raise ValueError(
                f"Unsupported project version {manifest.get('version')!r}; "
                f"this version supports {PROJECT_VERSION}."
            )
        try:
            with tempfile.TemporaryDirectory(prefix="leed-studio-open-") as temp_dir:
                array_path = Path(temp_dir) / "arrays.npz"
                with archive.open("arrays.npz", "r") as source, array_path.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                # NPZ is itself a ZIP. Inspect its member sizes before NumPy allocates
                # arrays, preventing an unexpectedly large decompressed allocation.
                total_uncompressed = 0
                with zipfile.ZipFile(array_path, "r") as nested:
                    members = nested.infolist()
                    if len(members) > len(ALLOWED_ARRAYS):
                        raise ValueError("Project contains too many array members.")
                    for member in members:
                        if member.file_size > MAX_TOTAL_UNCOMPRESSED_ARRAY_BYTES:
                            raise ValueError("A project array is too large to load safely.")
                        total_uncompressed += member.file_size
                    if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_ARRAY_BYTES:
                        raise ValueError("Uncompressed project arrays exceed the safe size limit.")
                with np.load(array_path, allow_pickle=False) as stored:
                    if not set(stored.files).issubset(ALLOWED_ARRAYS):
                        raise ValueError("Project contains unrecognized array names.")
                    arrays = {name: np.array(stored[name], copy=True) for name in stored.files}
        except Exception as exc:
            raise ValueError(f"Could not read project arrays: {exc}") from exc

    expected = manifest.get("arrays", {})
    if set(arrays) != set(expected):
        raise ValueError("Project array names do not match the manifest.")
    for name, arr in arrays.items():
        descriptor = expected[name]
        if not isinstance(descriptor, dict):
            raise ValueError(f"Project array descriptor for {name!r} must be an object.")
        if arr.dtype.hasobject or arr.dtype.kind not in "biuf":
            raise ValueError(f"Project array {name!r} has an unsupported dtype.")
        if arr.ndim > 4 or any(int(dimension) < 1 for dimension in arr.shape):
            raise ValueError(f"Project array {name!r} has an invalid shape.")
        if list(arr.shape) != descriptor.get("shape") or str(arr.dtype) != descriptor.get("dtype"):
            raise ValueError(f"Project array {name!r} does not match its manifest descriptor.")
    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Project metadata must be a JSON object.")
    return arrays, metadata
