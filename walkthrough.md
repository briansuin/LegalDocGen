# Walkthrough - Export & Validation Features

## 1. Export Templates
I have added the "Export Templates" feature which allows you to export selected templates to a folder named after the project.

### Verification Steps
1.  Run the application.
2.  Open **Legal Counsel** (or any project).
3.  Go to the **"模板与输入区设置"** tab.
4.  Select the templates you want to export (or check "Select/Deselect All").
5.  Click the new **"导出模板文件"** button.
6.  Choose a valid directory (e.g. Desktop).
7.  Verify that a folder named "Legal Counsel" appeared in the chosen directory and contains the selected `.docx` files.

---

## 2. Field Name Validation
I have added validation to ensure input area names are valid Python variables. This prevents errors during document generation.

### Verification Steps
1.  Go to **"模板与输入区设置"** tab.
2.  Click **"添加新的输入区"**.
3.  **Test Invalid Names** (Should show warning):
    - `123test` (Starts with number)
    - `test-var` (Contains hyphen)
    - `my var` (Contains space)
4.  **Test Valid Names** (Should succeed):
    - `client_name`
    - `甲方姓名` (Chinese characters are allowed)
