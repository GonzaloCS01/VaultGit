# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


ROOT = Path(SPECPATH).resolve().parent

NACL_DATAS, NACL_BINARIES, NACL_HIDDENIMPORTS = collect_all(
    "nacl"
)


a = Analysis(
    [str(ROOT / "src" / "gui.py")],
    pathex=[
        str(ROOT / "src"),
    ],
    binaries=NACL_BINARIES,
    datas=[
        (
            str(ROOT / "assets"),
            "assets",
        ),
        *NACL_DATAS,
    ],
    hiddenimports=[
        "_cffi_backend",
        *NACL_HIDDENIMPORTS,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(
    a.pure
)


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="VaultGit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(
        ROOT / "assets" / "vaultgit.ico"
    ),
    version=str(
        ROOT
        / "packaging"
        / "version_info.txt"
    ),
)
