
import sys
import os
import zipfile
from docxtpl import DocxTemplate

# Path to the file
file_path = r"d:\LegalDocGen\templates\顾问案件\3.常年法律顾问合同.docx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

print(f"Analyzing {file_path}...")

xml_content = ""

try:
    print("Trying docxtpl...")
    tpl = DocxTemplate(file_path)
    # Some versions require parsing first or have different init
    xml_content = tpl.get_xml()
except Exception as e:
    print(f"docxtpl error: {e}")
    print("Falling back to zipfile...")
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml').decode('utf-8')
    except Exception as z_e:
        print(f"zipfile error: {z_e}")
        sys.exit(1)

if not xml_content:
    print("Could not get XML content.")
    sys.exit(1)

print(f"XML length: {len(xml_content)}")
error_index = 87171

if error_index >= len(xml_content):
    print(f"Index {error_index} is out of bounds. Length is {len(xml_content)}")
else:
    start = max(0, error_index - 150)
    end = min(len(xml_content), error_index + 150)
    
    snippet = xml_content[start:end]
    print(f"Snippet around {error_index}:")
    print(snippet)
    print("-" * 40)
    # Calculate relative position in snippet for visualization
    rel_pos = error_index - start
    pointer = " " * rel_pos + "^"
    print(snippet)
    print(pointer)
    print(f"Char at {error_index}: '{xml_content[error_index]}'")
