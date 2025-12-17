# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Alert Alchemy.

This creates a single-file executable with incidents bundled inside.
Usage: pyinstaller build/alert-alchemy.spec
"""

import os
from pathlib import Path

# Get the repo root (parent of build/)
repo_root = Path(SPECPATH).parent

block_cipher = None

# Collect data files
datas = [
    # Bundle incidents folder
    (str(repo_root / 'incidents'), 'incidents'),
]

# Optionally include docs
docs_file = repo_root / 'docs' / 'write-an-incident.md'
if docs_file.exists():
    datas.append((str(docs_file), 'docs'))

a = Analysis(
    [str(repo_root / 'src' / 'alert_alchemy' / '__main__.py')],
    pathex=[str(repo_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'alert_alchemy',
        'alert_alchemy.cli',
        'alert_alchemy.engine',
        'alert_alchemy.loader',
        'alert_alchemy.models',
        'alert_alchemy.render',
        'alert_alchemy.scoring',
        'alert_alchemy.state',
        'alert_alchemy.util',
        'typer',
        'rich',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='alert-alchemy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
