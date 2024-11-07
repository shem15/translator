# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['translator.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('res', 'res'),  # Include res folder containing icons
        ('poppler', 'poppler'),  # Include poppler directory
        ('prompts.py', '.'),  # Include prompts.py
        ('ai_utils.py', '.'),  # Include ai_utils.py
        ('config.py', '.'),  # Include config.py
        ('encrypted_api_key.json', '.'),  # Include API key file
        ('secret.key', '.'),  # Include encryption key
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='translator-experimental',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
