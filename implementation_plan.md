# Mail Merge Feature Implementation Plan

## Goal Description
Add a "Mail Merge" (Batch Generation) feature to the application. This allows users to users to upload an Excel file (containing data like Name, Gender, etc.) and a Word template, and generate multiple documents at once—one for each row in the Excel file.

## User Review Required
> [!IMPORTANT]
> **Dependency Addition**: adding `openpyxl` to `requirements.txt` to read Excel files. This is lighter than `pandas` and sufficient for the task.

## Proposed Changes

### Configuration
#### [MODIFY] [requirements.txt](file:///d:/Programing/LegalDocGen/requirements.txt)
- Add `openpyxl`
- Add `odfpy` (for ODS support)

### Source Code

#### [MODIFY] [src/views/batch_tab.py](file:///d:/Programing/LegalDocGen/src/views/batch_tab.py)
- **UI Updates**:
    - **File Loading**: Update filter to include `*.ods` and `*.xlsx`, `*.xls`.
    - **Filename Selection**: Replace single ComboBox with a new layout allowing users to select *multiple* columns to compose the filename. Use a ListWidget with checkboxes.
    - **Output Details**: Update UI to reflect that a subfolder will be created.
- **Logic Updates**:
    - `load_excel()`: Add logic to read `.ods` files using `odfpy`.
    - `generate()`: 
        - Filename Construction: Join values of all selected columns (e.g., "Name_Gender").
        - **Auto-Subfolder**: Create a directory `Batch_Output_{Date_Time}` inside the selected output folder and save files there.

#### [MODIFY] [src/views/main_window.py](file:///d:/Programing/LegalDocGen/src/views/main_window.py)
- Import `BatchTab`.
- Add "📧 批量生成" (Batch Generate) tab to `self.tabs` in `setup_ui`.
- Enable this tab by default (or manage its state).

## Verification Plan

### Automated Tests
- None currently exist for UI.
- Verify `openpyxl` installation by running the built app or python script.

### Manual Verification
1.  **Setup**: Prepare an Excel file (`test.xlsx`) with columns `Name`, `Gender` and 3 rows of data. Prepare a Word template (`invite.docx`) with `{{Name}}` and `{{Gender}}`.
2.  **Launch**: Run `python main.py`.
3.  **UI Check**: Verify "批量生成" tab exists.
4.  **Workflow**:
    - Select `test.xlsx`. Verify preview shows data correctly.
    - Select `invite.docx`.
    - Select Output Folder.
    - Click Generate.
5.  **Result**: Check Output Folder. Should contain 3 `.docx` files named after the `Name` column. Open one to verify `{{Name}}` and `{{Gender}}` are replaced correcty.
