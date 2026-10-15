from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_release_files_and_user_documentation_are_present():
    required = [
        ROOT / "LEED_Studio.spec",
        ROOT / "run_leed_studio.py",
        ROOT / "packaging" / "LEED-Studio.iss",
        ROOT / "build_windows.bat",
        ROOT / ".github" / "workflows" / "windows-build.yml",
        ROOT / "SOFTWARE_OVERVIEW_AND_USER_MANUAL.md",
        ROOT / "CREDITS.md",
        ROOT / "WINDOWS_GUI_GUIDE.md",
        ROOT / "leed_studio" / "data" / "sample_drifting_stack.tif",
        ROOT / "leed_studio" / "data" / "leed_studio.ico",
    ]
    assert all(path.is_file() for path in required), [
        str(path) for path in required if not path.is_file()
    ]


def test_release_versions_are_consistent():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (ROOT / "leed_studio" / "__init__.py").read_text(encoding="utf-8")
    installer = (ROOT / "packaging" / "LEED-Studio.iss").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "windows-build.yml").read_text(encoding="utf-8")
    assert 'version = "0.11.1"' in pyproject
    assert '__version__ = "0.11.1"' in package_init
    assert '#define MyAppVersion "0.11.1"' in installer
    assert "LEED-Studio-Setup-0.11.1.exe" in workflow
    assert "LEED-Studio-Portable-0.11.1.zip" in workflow


def test_windows_workflow_checks_frozen_exe_and_installer():
    workflow = (ROOT / ".github" / "workflows" / "windows-build.yml").read_text(encoding="utf-8")
    assert '["run_leed_studio.py"]' in (ROOT / "LEED_Studio.spec").read_text(encoding="utf-8")
    assert "PyInstaller" in workflow
    assert "--self-test-gui" in workflow
    assert "Test install, launch, and uninstall" in workflow
    assert "QT_QPA_PLATFORM: offscreen" in workflow
    assert "WINDOWS_ACCEPTANCE_TESTS.txt" in workflow


def test_entrypoint_has_noninteractive_packaged_gui_test():
    entry = (ROOT / "leed_studio" / "__main__.py").read_text(encoding="utf-8")
    assert "--self-test-gui" in entry
    assert "--self-test-core" in entry
    assert "track_spot_series" in entry
    assert "sample_drifting_stack.tif" in entry
    assert "window.run_fit()" in entry
    assert "window.run_series()" in entry
