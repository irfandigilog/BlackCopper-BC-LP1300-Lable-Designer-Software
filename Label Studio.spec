# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['python\\main_window.py'],
    pathex=['python'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'PyQt6.sip',
        # App modules
        'canvas',
        'engine',
        'printer',
        'scan_hardware',
        'scan_win32_printers',
        'license_manager',
        # QR Code generation
        'qrcode',
        'qrcode.image.base',
        'qrcode.image.pure',
        'qrcode.image.styledpil',
        'qrcode.image.svg',
        'qrcode.constants',
        'qrcode.exceptions',
        'qrcode.util',
        # Barcode generation
        'barcode',
        'barcode.writer',
        'barcode.codex',
        'barcode.isxn',
        'barcode.itf',
        'barcode.upc',
        'barcode.ean',
        'barcode.errors',
        # Pillow (image processing)
        'PIL',
        'PIL.Image',
        'PIL.BmpImagePlugin',
        'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        # PDF import (PyMuPDF)
        'fitz',
        # Windows printer
        'win32print',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Black Copper 03124002221',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Black Copper 03124002221',
)
