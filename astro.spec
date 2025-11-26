# -*- mode: python ; coding: utf-8 -*-
"""
ASTRO - Autonomous Agent Ecosystem
PyInstaller Specification File
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files
datas = [
    ('config', 'config'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Hidden imports for dynamic modules
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'aiofiles',
    'aiohttp',
    'aiosqlite',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'duckduckgo_search',
    'beautifulsoup4',
    'bs4',
    'openai',
    'yaml',
    'dotenv',
    'psutil',
    'numpy',
    'matplotlib',
]

# Add customtkinter data files
try:
    import customtkinter
    import os
    ctk_path = os.path.dirname(customtkinter.__file__)
    datas.append((ctk_path, 'customtkinter'))
except ImportError:
    pass

a = Analysis(
    ['src/gui_app.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='ASTRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
