import os
import sys
import subprocess
import shutil
import argparse

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not."""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully.")

def build_exe(one_file=False, console=False):
    """Build the executable using PyInstaller."""
    # Ensure PyInstaller is installed
    check_pyinstaller()
    
    # Clean previous build if exists
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Create spec file content with consistent field numbering
    binaries_part = "a.binaries, a.zipfiles, a.datas, " if one_file else ""
    exclude_binaries_value = "False" if one_file else "True"
    # Use proper Python boolean capitalization (True/False, not true/false)
    console_value = str(console).lower().capitalize()
    collect_part = "" if one_file else """
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MonitorBrightness',
)
"""
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['monitor.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5.sip'],
    hookspath=[],
    hooksconfig={{}},
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
    {binaries_part}
    [],
    exclude_binaries={exclude_binaries_value},
    name='MonitorBrightness',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={console_value},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)
{collect_part}
"""
    
    # Write spec file
    with open("MonitorBrightness.spec", "w") as f:
        f.write(spec_content)
    
    # Build using PyInstaller
    print(f"Building {'one-file' if one_file else 'directory-based'} executable with {'console' if console else 'no console'}...")
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "MonitorBrightness.spec"
    ])
    
    # Check if build was successful
    exe_path = os.path.join("dist", "MonitorBrightness.exe" if one_file else "MonitorBrightness", "MonitorBrightness.exe")
    if os.path.exists(exe_path):
        print(f"Build successful! Executable created at: {os.path.abspath(exe_path)}")
    else:
        print("Build failed. Executable not found.")

def build_installer_exe():
    """Build the installer executable."""
    # Ensure PyInstaller is installed
    check_pyinstaller()
    
    # Build using PyInstaller
    print("Building installer executable...")
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "--onefile",
        "--windowed",
        "installer.py",
        "--name", 
        "MonitorBrightnessInstaller"
    ])
    
    # Check if build was successful
    exe_path = os.path.join("dist", "MonitorBrightnessInstaller.exe")
    if os.path.exists(exe_path):
        print(f"Installer build successful! Executable created at: {os.path.abspath(exe_path)}")
    else:
        print("Installer build failed. Executable not found.")

def main():
    parser = argparse.ArgumentParser(description="Build Monitor Brightness application executable")
    parser.add_argument("--onefile", action="store_true", help="Build a single executable file")
    parser.add_argument("--console", action="store_true", help="Show console window when running")
    parser.add_argument("--installer", action="store_true", help="Build the installer executable")
    
    args = parser.parse_args()
    
    if args.installer:
        build_installer_exe()
    else:
        build_exe(one_file=args.onefile, console=args.console)

if __name__ == "__main__":
    main()
