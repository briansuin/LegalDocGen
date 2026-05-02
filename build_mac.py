
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
    # We use sys.executable to ensure we use the same python environment
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # macOS .app
        "--name", "LegalDocGen",
        # We manually copy templates to ensure structure control, so we don't use --add-data here
        "--hidden-import", "docxtpl",
        "main.py"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n--- PyInstaller Build Successful ---")
        
        # 4. Post-Build: Copy templates
        # Target: dist/LegalDocGen.app/Contents/MacOS/_internal/templates
        # This structure ensures src/utils.py (frozen logic) finds them.
        
        app_path = os.path.join("dist", "LegalDocGen.app")
        # Inside the .app, usage is: Contents/MacOS/LegalDocGen (exe)
        # So _internal is usually at Contents/MacOS/_internal (for onedir default in newer PyInstaller)
        
        # Verify structure if possible, but standard PyInstaller behavior for macOS windowed:
        contents_macos = os.path.join(app_path, "Contents", "MacOS")
        internal_dir = os.path.join(contents_macos, "_internal")
        dest_templates = os.path.join(internal_dir, "templates")
        src_templates = "templates"
        
        if os.path.exists(src_templates):
            print(f"Copying templates to {dest_templates}...")
            # Ensure parent exists (it should if PyInstaller ran correctly)
            if not os.path.exists(internal_dir):
                os.makedirs(internal_dir, exist_ok=True)
                
            shutil.copytree(src_templates, dest_templates, dirs_exist_ok=True)
            print("Templates copied successfully.")
        else:
            print("Warning: 'templates' directory not found in source.")

        # Copy Citation Library
        dest_citation = os.path.join(internal_dir, "citation")
        src_citation = "citation"
        
        if os.path.exists(src_citation):
            print(f"Copying citation library to {dest_citation}...")
            if not os.path.exists(internal_dir):
                os.makedirs(internal_dir, exist_ok=True)
            shutil.copytree(src_citation, dest_citation, dirs_exist_ok=True)
            print("Citation library copied successfully.")
        else:
            print("Warning: 'citation' directory not found in source. Creating empty directory.")
            os.makedirs(dest_citation, exist_ok=True)

        print("\n--- macOS Build Complete ---")
        print(f"App Bundle: {app_path}")
        print("You can run it by double-clicking or: open dist/LegalDocGen.app")
        
    except subprocess.CalledProcessError as e:
        print(f"Build Failed: {e}")

if __name__ == "__main__":
    run_build()
