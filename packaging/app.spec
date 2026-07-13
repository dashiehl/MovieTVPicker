# PyInstaller spec for Watch Picker.
# Build from the project root: pyinstaller packaging/app.spec
# Output lands in dist/WatchPicker/ — copy that whole folder anywhere to run it.

import os

block_cipher = None
project_root = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))

a = Analysis(
    [os.path.join(project_root, "main.py")],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, "data", "catalog.json"), "data"),
        (os.path.join(project_root, "scripts", "catalog_seed.json"), "scripts"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WatchPicker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WatchPicker",
)
