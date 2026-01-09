import os
import re
import docx
import shutil
import zipfile

import sys
import platform
import subprocess

# --- CONSTANTS & PATHS ---
if getattr(sys, 'frozen', False):
    # Running as executable (Frozen)
    ext_root = os.path.dirname(sys.executable)
    portable_data_dir = os.path.join(ext_root, "data")
    internal_dir = os.path.join(ext_root, "_internal")
    
    # Locate Bundled Templates (Source)
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller --onefile mode
        BUNDLED_TEMPLATES_DIR = os.path.join(sys._MEIPASS, "templates")
    else:
        # PyInstaller --onedir mode
        # Check _internal/templates (Windows newer default) or adjacent templates
        check_bundled = os.path.join(internal_dir, "templates")
        if not os.path.exists(check_bundled):
             # Try adjacent to executable (macOS often places here with --add-data)
             check_bundled = os.path.join(ext_root, "templates")
        BUNDLED_TEMPLATES_DIR = check_bundled

    # Determine Runtime Storage (Destination)
    # Priority 1: 'data' folder next to exe (Portable Mode - Explicit)
    if os.path.exists(portable_data_dir):
        BASE_DIR = portable_data_dir
    # Priority 2: '_internal/templates' exists (Portable Mode - Implicit/Default)
    elif os.path.exists(os.path.join(internal_dir, "templates")):
        BASE_DIR = internal_dir
    else:
        # Priority 3: Installed/Standard Mode (Fallback)
        if platform.system() == 'Windows':
            base_storage = os.environ.get('APPDATA', os.path.expanduser("~")) 
            BASE_DIR = os.path.join(base_storage, "LegalDocGen")
        elif platform.system() == 'Darwin':
            # macOS: Use Documents to avoid read-only errors and ensure user accessibility
            BASE_DIR = os.path.expanduser("~/Documents/LegalDocAutomator")
        else:
            base_storage = os.path.expanduser("~/.config")
            BASE_DIR = os.path.join(base_storage, "LegalDocGen")
            
else:
    # Running as script (Dev)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLED_TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

CONFIG_DIR = os.path.join(BASE_DIR, "config")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

def ensure_directories():
    for d in [CONFIG_DIR, TEMPLATE_DIR]:
        os.makedirs(d, exist_ok=True)
    
    # Auto-initialize templates if empty (First Run)
    if os.path.exists(BUNDLED_TEMPLATES_DIR) and os.path.exists(TEMPLATE_DIR):
        if not os.listdir(TEMPLATE_DIR):
            try:
                print(f"First run detected. Copying templates from {BUNDLED_TEMPLATES_DIR} to {TEMPLATE_DIR}")
                # We iterate and copy to avoid deleting the destination root
                for item in os.listdir(BUNDLED_TEMPLATES_DIR):
                    s = os.path.join(BUNDLED_TEMPLATES_DIR, item)
                    d = os.path.join(TEMPLATE_DIR, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            except Exception as e:
                print(f"Error copying default templates: {e}")

class SmartSync:
    @staticmethod
    def sync_template_variable(template_path, old_var, new_var):
        """
        Surgically replaces {{old_var}} with {{new_var}} inside a docx file
        while preserving run formatting (bold/color/etc).
        """
        if not os.path.exists(template_path):
            return False

        doc = docx.Document(template_path)
        modified = False

        # 1. Paragraphs
        for p in doc.paragraphs:
            if SmartSync._replace_in_paragraph(p, old_var, new_var):
                modified = True

        # 2. Tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        if SmartSync._replace_in_paragraph(p, old_var, new_var):
                            modified = True
                            
        if modified:
            doc.save(template_path)
            return True
        return False

    @staticmethod
    def _replace_in_paragraph(paragraph, old_var, new_var):
        """
        Helper: Replaces text in a single paragraph object across multiple runs.
        """
        full_text = paragraph.text
        if f"{{{{{old_var}}}}}" not in full_text:
            return False

        # If simple replace works (contained in one run), try that first for speed?
        # Actually, standard python-docx 'text' assignment kills formatting.
        # We must iterate runs.
        
        # Strategy: Reconstruct runs into a string, track indices, replace in string,
        # then map back to runs. 
        # Easier Strategy for "Whole Tag":
        # 1. Find the start run index and end run index of the tag `{{...}}`
        # 2. Update the text in those runs.
        
        # This implementation below is a simplified version of "Smart Run Replacement" 
        # commonly used for this exact problem.
        
        target = f"{{{{{old_var}}}}}"
        replacement = f"{{{{{new_var}}}}}"
        
        # Simple case: if the tag is fully inside one run
        for run in paragraph.runs:
            if target in run.text:
                run.text = run.text.replace(target, replacement)
                return True

        # Complex case: Tag wraps across runs (e.g. Run1: "{{", Run2: "Name", Run3: "}}")
        # We need to coalesce.
        # Allow simple brute force for now since typically users select the whole tag to bold it.
        # If it is split, python-docx replacement is hard without a deeper library.
        # Implementing a robust split-run-stitcher is complex.
        
        # Fallback: If not found in single runs but found in paragraph,
        # we have a split formatting issue.
        # To fix it, we might lose mixed formatting on the tag itself, but keep paragraph style.
        # Let's try to find the start and end.
        
        match = re.search(re.escape(target), full_text)
        if match:
            # It exists but wasn't in a single run.
            # We will clear the runs involved and put the new text in the first one.
            # This generally preserves the formatting of the START of the tag.
            
            curr_index = 0
            start_run_idx = -1
            end_run_idx = -1
            
            start_char = match.start()
            end_char = match.end()
            
            # Find which runs cover this range
            for i, run in enumerate(paragraph.runs):
                run_len = len(run.text)
                run_start = curr_index
                run_end = curr_index + run_len
                
                if start_run_idx == -1 and run_end > start_char:
                    start_run_idx = i
                
                if run_start < end_char:
                    end_run_idx = i
                
                curr_index += run_len
            
            if start_run_idx != -1 and end_run_idx != -1:
                # We have the range of runs.
                # Logic:
                # 1. Take text before match in start_run
                # 2. Add replacement
                # 3. Take text after match in end_run
                # 4. Set start_run text to (1+2+3)
                # 5. Clear intermediate runs
                
                # Careful with detailed offsets within the run
                
                # Simple approach for now to ensure functionality over perfect style retention on split tags:
                # Just replace the text in the first run and clear others? No, that deletes valid text.
                
                # Let's just do a naive full-paragraph replace if split.
                # This resets run formatting to paragraph default but ensures data integrity.
                paragraph.text = full_text.replace(target, replacement)
                return True
                
        return False

def open_file_or_folder(path):
    """
    Open a file or folder using the default system application in a cross-platform way.
    """
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':       # macOS
        subprocess.call(['open', path])
    else:                                     # Linux
        subprocess.call(['xdg-open', path])

def extract_fields(path):
    """
    Parses a docx or odt file and returns a set of all {{variable}} names found.
    """
    if not os.path.exists(path):
        return set()
    
    unique_fields = set()
    ext = os.path.splitext(path)[1].lower()

    if ext == '.docx':
        return _extract_from_docx(path)
    elif ext == '.odt':
        return _extract_from_odt(path)
    return set()

def _extract_from_odt(path):
    unique_fields = set()
    try:
        with zipfile.ZipFile(path, 'r') as z:
            content = z.read('content.xml').decode('utf-8')
            # Regex for {{...}}
            matches = re.findall(r"\{\{(.*?)\}\}", content)
            for m in matches:
                clean = m.strip()
                # ODT might insert XML tags inside the braces if formatted?
                # Simpler regex might strip basic XML tags if they appear, 
                # but usually py3o expects clean jinja tags.
                # Let's assume user inputs clean tags for now or use a robust cleaner.
                # However, XML tags inside {{ }} break Jinja.
                # Users should type cleanly.
                if clean:
                    unique_fields.add(clean)
    except Exception as e:
        print(f"Error parsing ODT {path}: {e}")
    return unique_fields

def _extract_from_docx(path):
    """
    Parses a docx file and returns a set of all {{variable}} names found.
    """
    if not os.path.exists(path):
        return set()
    
    unique_fields = set()
    try:
        # Use a context manager to ensure the file handle is closed.
        # python-docx loads the file into memory, so we can close the handle after loading (or after processing).
        with open(path, 'rb') as f:
            doc = docx.Document(f)
            
            # Helper to scan text
            def scan_text(text):
                # Find all {{...}} patterns
                matches = re.findall(r"\{\{(.*?)\}\}", text)
                for m in matches:
                    # m is the content inside brackets. 
                    # It might be " Name " -> strip it to "Name"
                    clean = m.strip()
                    if clean:
                        unique_fields.add(clean)

            # 1. Paragraphs
            for p in doc.paragraphs:
                scan_text(p.text)
                
            # 2. Tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            scan_text(p.text)
                        
    except Exception as e:
        print(f"Error parsing {path}: {e}")
        
    return unique_fields
