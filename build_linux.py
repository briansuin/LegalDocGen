
import os
import sys
import subprocess
import shutil

def run_build():
    print("--- Building LegalDocGen for Linux ---")
    
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
    # Linux uses : separator for paths, but PyInstaller --add-data uses src:dest syntax which is platform-agnostic usually,
    # but strictly on Linux it is SRC:DEST. On Windows it is SRC;DEST.
    # PyInstaller handles checking the separator but it's safer to be explicit or use os.pathsep if constructing manually.
    # Actually, the --add-data argument syntax is 'SOURCE:DEST' on Linux/Mac and 'SOURCE;DEST' on Windows.
    add_data_sep = ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--noconsole",  # GUI mode
        "--name", "LegalDocGen",
        # We manually copy templates to _internal/templates, so no --add-data needed here
        "main.py"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n--- PyInstaller Build Successful ---")
        
        # 4. Post-Build: Copy templates
        # We need to copy 'templates' to 'dist/LegalDocGen/_internal/templates'
        # PyInstaller (onedir) structure:
        # dist/
        #   LegalDocGen/
        #     LegalDocGen (executable)
        #     _internal/ (libs and pinned data)
        
        # Wait, usually _internal is where PyInstaller dumps things in newer versions.
        # Let's verify where to put it. 
        # utils.py says: 
        # internal_dir = os.path.join(ext_root, "_internal")
        # elif os.path.exists(os.path.join(internal_dir, "templates")): ...
        
        dest_dir = os.path.join("dist", "LegalDocGen", "_internal", "templates")
        src_dir = "templates"
        
        if os.path.exists(src_dir):
            print(f"Copying templates from {src_dir} to {dest_dir}...")
            # Cop tree handles creation of dest directory usually if it doesn't exist, 
            # but shutil.copytree requires dict not to exist for Python < 3.8. 
            # For safety, let's use copytree with dirs_exist_ok=True (available in 3.8+)
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            print("Templates copied successfully.")
        else:
            print("Warning: 'templates' directory not found in source.")
            
        print("\n--- Linux Build Complete ---")
        print("Executable is located at: dist/LegalDocGen/LegalDocGen")
        
    except subprocess.CalledProcessError as e:
        print(f"Build Failed: {e}")

if __name__ == "__main__":
    run_build()
