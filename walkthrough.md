# Mail Merge Feature Walkthrough

I have implemented the **Mail Merge (Batch Generation)** feature, allowing you to generate multiple documents from an Excel list and a Word/ODT template.

## Feature Overview

A new tab **"📧 批量生成"** has been added to the main window.

## Feature Overview

A new tab **"📧 批量生成"** has been added to the main window.

### Key Components
1.  **File Selection**:
    - **Data Source**: Upload your `.xlsx`, `.xls` (Excel) or `.ods` (LibreOffice) file. **(Supports Drag & Drop)**
    - **Template File**: Upload your `.docx` or `.odt` template. **(Supports Drag & Drop)**
2.  **Data Preview**:
    - Verify your data is loaded correctly in the preview table.
    - **Filename Columns**: Select one or more columns to construct the output filename. 
    - **Quick Copy**: Click on any column name (e.g., "姓名") to automatically copy its template variable (e.g., `{{姓名}}`) to your clipboard.
    - **Filename Affixes**: (Optional) Add a Prefix (e.g., `2024_`) or Suffix (e.g., `_Invitation`) to the filename.
3.  **Generation**:
    - Select an output folder.
    - Click **"🚀 开始批量生成"** to process all rows.
    - **Auto-Subfolder**: Files are automatically saved in a new subfolder (e.g., `批量生成_20240101_120000`) inside your selected directory.

## Technical Details

- **Dependencies**: 
    - `openpyxl` for Excel files.
    - `odfpy` for LibreOffice ODS files.
- **Support**: 
    - Templates: `.docx`, `.odt`
    - Data: `.xlsx`, `.xls`, `.ods`
- **Logic**: 
    - Supports multi-column filename generation (joined by underscore).
    - Automatically creates time-stamped subfolders to organize outputs.
    - Matches column headers to template variables exactly.

## How to Use

1.  Prepare a data file (Excel or ODS) with headers.
2.  Prepare a Word/ODT template with matching variables (e.g., `{{Name}}`).
3.  Open the app -> "Batch Generation".
4.  Load files.
5.  Check the boxes for columns you want in the filename (e.g., Name).
6.  Select base output folder.
7.  Run! Output will be in a new subfolder.
