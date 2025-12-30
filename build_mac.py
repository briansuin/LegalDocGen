
import os
import sys
import subprocess
import shutil

def run_build():
    print("--- Building LegalDocGen for macOS ---")
    
    # 1. Check dependencies
    try:
        import PyInstaller
        import docxtpl
        import PyQt6
        print("Dependencies check passed.")
    except ImportError as e:
        print(f"Error: Missing dependency {e.name}. Please run: pip install pyinstaller docxtpl PyQt6")
        return

    # 2. Cleanup previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # 3. Define PyInstaller command
    # Separator: : on Unix, ; on Windows.
    sep = os.pathsep 
    
    # We include 'src' source code because docxtpl might need it or our dynamic imports?
    # Actually, main.py imports src. PyInstaller analyzes this.
    # explicit imports usually not needed if code is reachable.
    # But --add-data is for non-code files.
    # The 'src' folder IS the code. PyInstaller should bundle it as bytecode/library.
    # However, `docxtpl` is a hidden import sometimes.
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # macOS .app
        "--name", "LegalDocGen",
        "--add-data", "templates:templates", # Bundle templates folder
        "--hidden-import", "docxtpl",
        # If you have an icon:
        # "--icon", "assets/icon.icns", 
        "main.py"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n--- Build Successful ---")
        print("Executable is located at: dist/LegalDocGen.app")
        print("You can run it by double-clicking or: open dist/LegalDocGen.app")
        
    except subprocess.CalledProcessError as e:
        print(f"Build Failed: {e}")

if __name__ == "__main__":
    run_build()
