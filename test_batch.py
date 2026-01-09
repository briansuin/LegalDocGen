import os
import openpyxl
from docxtpl import DocxTemplate
from src.odt_renderer import OdtTemplate

def test_logic():
    print("Testing Logic...")
    
    # 1. Create dummy Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Name", "Type"])
    ws.append(["Alice", "A"])
    ws.append(["Bob", "B"])
    wb.save("test_data.xlsx")
    print("Created test_data.xlsx")
    
    # 2. Create dummy DOCX template
    doc = DocxTemplate("d:\\Programing\\LegalDocGen\\src\\debug_template.py") # Use existing file as base? No, need actual docx
    # We can't easily create a valid docx from scratch without a library or file.
    # But we can try to use a template from the project if one exists.
    # d:\Programing\LegalDocGen\templates has templates?
    
    template_dir = "d:\\Programing\\LegalDocGen\\templates"
    if not os.path.exists(template_dir):
        print("Template dir not found, skipping render test.")
        return

    files = os.listdir(template_dir)
    docx_files = [f for f in files if f.endswith(".docx")]
    
    if docx_files:
        t_path = os.path.join(template_dir, docx_files[0])
        print(f"Using template: {t_path}")
        
        # Test DocxTemplate load
        try:
            tpl = DocxTemplate(t_path)
            print("DocxTemplate init success")
            tpl.render({"Name": "Alice"})
            tpl.save("test_output.docx")
            print("Docx Render success")
        except Exception as e:
            print(f"Docx Error: {e}")

    # Test ODT logic import
    try:
        from src.odt_renderer import OdtTemplate
        print("OdtTemplate import success")
    except ImportError as e:
        print(f"ODT Import Error: {e}")
        
    print("Done.")

if __name__ == "__main__":
    test_logic()
