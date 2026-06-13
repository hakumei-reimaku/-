# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置
在 Windows 上执行:
    pyinstaller SimpleMusicPlayer.spec --clean --noconfirm
即可在 dist/ 下生成单文件 SimpleMusicPlayer.exe
"""
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 收集 pygame / mutagen / PyQt5 的必要数据
datas = []
# pygame 需要 SDL 相关资源(可选,部分环境需要)
try:
    import pygame
    datas += collect_data_files('pygame')
except Exception:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pygame', 'mutagen', 'PyQt5'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'PySide2', 'PySide6', 'scipy',
    ],
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
    name='SimpleMusicPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # GUI 程序, 不显示黑色控制台
    disable_windowed_traceback=False,
    target_arch=None,         # 跟随宿主机器 (Windows 上默认 x86_64)
    codesign_identity=None,
    entitlements_file=None,
)
