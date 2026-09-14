"""
Build script to compile PDF Studio Pro into a standalone Windows .exe folder
with NO console window, custom app icon, and all bundled assets.
"""

import os
import sys
import shutil
import PyInstaller.__main__

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
    main_script = os.path.join(base_dir, "main.py")

    print("=" * 60)
    print("[*] Building Standalone Windows Executable for PDF Studio Pro...")
    print("=" * 60)

    # PyInstaller arguments
    args = [
        main_script,
        "--name=PDF Studio Pro",
        "--noconsole",          # Absolutely NO Command Prompt / Terminal window on launch
        "--onedir",             # Creates a portable standalone folder that works on any PC
        "--windowed",
        "--noconfirm",
        "--clean",
        "--noupx",
        f"--icon={icon_path}",
        "--add-data=assets;assets",
        "--collect-all=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=torchaudio",
        "--exclude-module=tensorflow",
        "--exclude-module=keras",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=numpy",
        "--exclude-module=matplotlib",
        "--exclude-module=pytest",
        "--exclude-module=openpyxl",
        "--exclude-module=h5py",
        "--exclude-module=numba",
        "--exclude-module=llvmlite",
        "--exclude-module=lxml",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=sympy",
        "--exclude-module=sklearn",
        "--exclude-module=cryptography",
        "--exclude-module=bcrypt",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}"
    ]

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    print("[SUCCESS] Build Completed Successfully!")
    print(f"[+] Standalone App Folder: {os.path.join(dist_dir, 'PDF Studio Pro')}")
    print(f"[+] Executable: {os.path.join(dist_dir, 'PDF Studio Pro', 'PDF Studio Pro.exe')}")
    print("=" * 60)

if __name__ == "__main__":
    build()
