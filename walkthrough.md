# Walkthrough - 盈科文书助手 (Yingke Document Assistant)

## Features Implemented

### 1. Sub-Input Fields (Hierarchy)
- **Concept**: Create nested fields (e.g., `Client` -> `Name`).
- **UI**: Added "Add Sub-Input" button in Settings.
- **Drafting**: Nested fields appear as GroupBoxes.
- **Flat Context**: Despite the UI hierarchy, variables map directly to their Leaf ID (e.g. `{{Name}}`), making templates simpler.

### 2. Field Management & Template Sync
- **Simplified UI**: The Settings tab now shows a single column "Field Name". This name serves as both the visible label and the internal Variable ID tag.
- **Edit Field**:
    -   Select a field -> Click "Edit Selected".
    -   Rename the field.
    -   **Auto-Sync**: Automatically updates `{{OldName}}` to `{{NewName}}` in all linked templates.
- **Delete Field**:
    -   Select a field -> Click "Delete Selected".
    -   **Auto-Sync**: Removes `{{Name}}` from templates.
- **Reorder**: Drag and drop fields in the tree to change their order in the "Drafting" form.
- **Formatting Preservation**: 
    -   Before: Renaming a tag could sometimes break the line's formatting (bold/font) if the tag was internally "split" by Word.
    -   Now: Implemented a **Stage-2 Smart Sync** algorithm that meticulously surgically replaces the text across multiple "runs" without resetting the line's formatting.

## Verification

### Automated Logic
- **Sync Test**: Verified that `{{tag}}` and `{{ tag }}` variants are correctly identified and replaced using Regular Expressions.
- **Formatting**: Verified that replacing tags preserves surrounding bold/italic formatting, even when tags are split across multiple runs (e.g., `{{` is Red and `Tag` is Blue).

### User Guide
1.  **Add**: Use "Add (Root)" or "Add Sub-Input". Enter the Name (e.g. "Client Name").
2.  **Edit**: Rename the field. The system handles the rest.
## How to Run

1.  **Run the Application**:
    ```bash
    python main.py
    ```
    *(Old `app.py` has been refactored into `main.py` and `src/` directory)*

2.  **Usage**:
### 3. Template Management
- **Project Isolation**: Each project now has its own dedicated folder in `templates/<project_id>/`.
- **Import**: Click "Add New Template" to copy a file from anywhere on your computer into this dedicated project folder.
- **Management**: All operations (opening, deleting, generating) automatically target this specific folder. No need to manage files in Explorer.
- **Selection**:
- **Selection**:
    -   **Checkboxes**: Each template now has a checkbox.
    -   **Reorder**: Drag and drop templates in the list to change their processing order.
    -   **Generation Control**: Only *checked* templates will be generated when clicking "Generate Documents".
- **Delete**: Remove templates from the project or disk.

### 4. Project Safety & Management
- **Overwrite Protection**: The system prevents creating a project if the name already exists.
- **Context Menu (Right-Click)**:
    -   **Rename**: Right-click a project to rename it. 
        -   **Full Sync**: This will rename both the project configuration AND the underlying template directory in `templates/`. Your files move with the name.
    -   **Delete**: Right-click to permanently delete a project and all its templates.

## Document Generation
1.  **Drafting**: Fill in the form fields.
2.  **Selection**: Ensure desired templates are checked in Settings.
3.  **Generate**: Click "generate documents".
    -   **Validation**: The system checks if all fields are filled. If any are empty, it will stop and warn you. This ensures no `{{tag}}` placeholders are left in your documents.
    -   **One Step**: A "Save As" dialog appears (defaults to Desktop).
    -   **Action**: 
        -   To start valid defaults: Just click Save.
        -   To customize: Type a new name (e.g. `MyCase`) and click Save. This creates a new folder.
    -   **Output**: Files are saved into that folder.
4.  **Done**: The folder opens automatically.

### 5. Cross-Platform Support
- **Universal Opening**: Implemented logic to automatically open files and folders on **Windows**, **macOS**, and **Linux**.
	- Windows: `os.startfile`
	- macOS: `open` command
	- Linux: `xdg-open` command

### 6. Auto-Sync (File System Driven)
- **Concept**: The file system now drives the project configuration.
- **Project Discovery & Pruning**: 
    -   Simply copy a folder into `templates/` to create a Project.
    -   Delete a folder from `templates/` to **automatically delete** the project from the app.
- **Template Sync**: Copy `.docx` files into a project's folder. The app automatically adds them to the project.
- **Field Extraction (Strict)**: The app parses templates for `{{Variables}}`. It ensures the "Input Fields" list *exactly matches* the variables used. Unused fields are automatically removed.

### 7. Accessibility
- **Keyboard Shortcuts**:
    -   **Tab Navigation**: Pressing `Tab` cycles through input fields and lands on the "Generate Documents" button.
    -   **Quick Finish**: Pressing `Enter` on the *last* input field automatically moves focus to the "Generate Documents" button. You can then press `Enter` again to generate.

### 8. Linux Support
- **Build Script**: Created `build_linux.py` to automate the Linux build process.
- **Dependencies**: Automatic check and installation of `pyinstaller`, `docxtpl`, and `PyQt6`.
- **Resource Management**: Ensures `templates` directory is correctly copied to the build output `dist/LegalDocGen/_internal/templates`.
- **Cross-Platform**: The application now supports Windows (`build.bat`), macOS (`build_mac.py`), and Linux (`build_linux.py`).

## How to Build on Linux
1.  Open a terminal in the project directory.
2.  Run the build script:
    ```bash
    python3 build_linux.py
    ```
    (Note: You may need to install dependencies with `pip install --break-system-packages pyinstaller docxtpl PyQt6` if running outside a virtual environment).
3.  The executable will be generated at `dist/LegalDocGen/LegalDocGen`.
