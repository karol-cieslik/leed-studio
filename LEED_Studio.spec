# PyInstaller spec for the Windows onedir distribution.
# Build on Windows with: pyinstaller --noconfirm LEED_Studio.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hiddenimports = collect_submodules("pyqtgraph")
datas = collect_data_files("leed_studio")

a = Analysis(
    ["run_leed_studio.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests", "numpy.tests", "scipy.tests"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LEED Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="leed_studio/data/leed_studio.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LEED Studio",
)
