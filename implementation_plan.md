# Implementation Plan - Field Management & Template Sync

## Goal Description
Allow users to **Edit** (Rename Label/ID) and **Delete** fields/sub-fields in the Settings tab. Crucially, these changes should automatically propagate to the linked Word (`.docx`) templates (e.g., renaming `{{old_id}}` to `{{new_id}}`).

## User Review Required
> [!WARNING]
> **Word Template Structure**: Word documents often split text like `{{my_var}}` into multiple XML "runs" (e.g., `{{`, `my`, `_`, `var`, `}}`) due to spellcheck or formatting. Simple find-and-replace might miss some tags. This implementation will use a best-effort text replacement on `paragraph.text`, but **users should manually verify complex templates**.

> [!IMPORTANT]
> **Delete Behavior**: When deleting a field, the system will attempt to remove the tag `{{deleted_id}}` from the templates completely. This might leave extra spaces or empty lines.

## Proposed Changes

### LegalDocGen

#### [MODIFY] [app.py](file:///d:/LegalDocGen/app.py)

1.  **UI Updates**:
    -   Add **"Edit"** and **"Delete"** buttons to the Settings tab (next to Add buttons).
    -   Enable them only when an item is selected.
    
2.  **Logic Updates**:
    -   `edit_field()`:
        -   Prompt for new Label and new ID.
        -   If ID changed:
            -   Update `project_data`.
            -   Call `sync_rename_in_templates(old_id, new_id)`.
    -   `delete_field()`:
        -   Confirm dialog.
        -   Remove from `project_data`.
        -   Call `sync_delete_in_templates(target_id)`.

3.  **Template Sync Helper (New Internal Helper)**:
    -   `sync_rename_in_templates(old_id, new_id)`:
        -   Iterate `project_data['templates']`.
        -   Open each with `python-docx`.
        -   Iterate Paragraphs and Tables.
        -   Replace `{{old_id}}` (and variants like `{{ old_id }}`) with `{{new_id}}`.
        -   Save.
    -   `sync_delete_in_templates(target_id)`:
        -   Similar to rename, but replace with empty string ``.

## Verification Plan

### Manual Verification
1.  **Setup**:
    -   Create a field `old_tag`.
    -   Add `{{old_tag}}` to a Word template.
2.  **Rename**:
    -   Edit `old_tag` -> `new_tag` in UI.
    -   Check if UI updates.
    -   Open Word template -> Verify it now says `{{new_tag}}`.
3.  **Delete**:
    -   Delete `new_tag`.
    -   Open Word template -> Verify the tag is gone.
