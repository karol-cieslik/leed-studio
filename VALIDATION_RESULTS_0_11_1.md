# LEED Studio 0.11.1 — validation and packaging status

Date: 2026-10-14

## Checks executed in the current environment

- `python -m compileall -q leed_studio tests tools`: passed.
- `python -m pytest -q -ra -p no:cacheprovider`: **47 passed, 1 skipped**.
- Wheel build with `pip wheel --no-deps --no-build-isolation`: passed.
- Source ZIP integrity check: performed during final packaging.
- Wheel contents and isolated import: checked separately (see release result below).

The one skipped test is `tests/test_gui_smoke.py`; PySide6 is unavailable in this environment, so the Qt GUI cannot be imported or launched here.

## Windows executable status

**Not built or run in this environment.** The repository includes a Windows CI workflow designed to compile the source, run the Qt offscreen tests, build the PyInstaller app, run a packaged `--self-test-gui` workflow, test normal startup, build the installer, install it into a temporary directory, run the installed EXE self-test, and uninstall.

The CI workflow must be executed on a Windows runner before any claim that the `.exe` or installer has passed. No Windows binary is included in this source release unless generated separately by that workflow.

## Scientific validation status

The packaged GUI self-test uses the included simulated drifting-spot TIFF. It is a packaging and workflow smoke test, not a scientific benchmark. Numerical comparison against the public TU Wien Fe2O3 experimental Spot Tracker outputs remains outstanding.

## Why this status is explicit

A source test suite cannot verify Windows Qt plugin bundling, Windows dialogs, installer behavior, display scaling, graphics drivers, or agreement with experimental data. These checks require the Windows CI runner and, for interactive usability, a real Windows desktop.
