# Add Field Name Validation

## Goal
Enforce valid Python identifier naming for input fields (variables) to prevent document generation errors.

## User Review Required
> [!NOTE]
> Variable names must start with a letter or underscore and contain only letters, numbers, and underscores. Invalid names will be rejected with a warning message.

## Proposed Changes

### `src/views/settings_tab.py`
- Import `re` module.
- Add `validate_field_name` helper method.
    - Regex: `^[a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*$` (Allowing Chinese characters as Python 3 supports them in identifiers, which is crucial for this Chinese app).
    - Actually, `docxtpl` uses Jinja2, which requires valid Python identifiers. Python 3 allows unicode in identifiers.
    - **Wait**, standard `re` `\w` matches unicode in Python 3 by default.
    - So check `name.isidentifier()`. This is the most robust Python way.
    - Also probably want to warn against starting with a number explicitly if `isidentifier()` is too broad or too strict? `isidentifier()` is perfect.
    - But user specifically mentioned "numbers or symbols". 
    - I will use `isidentifier()` and also check for keywords? No, keywords are fine in Jinja usually, but better safe.
    - Let's stick to `isidentifier()`.

- Update `add_field_to_project`:
    - Call validation before processing.
    - Show alert if invalid.
- Update `edit_field`:
    - Call validation before processing.
    - Show alert if invalid.

#### [MODIFY] [settings_tab.py](file:///d:/ProgramingProjects/LegalDocGen/src/views/settings_tab.py)
- Import `keyword`.
- Add validation logic in `add_field_to_project` and `edit_field`.

## Verification Plan

### Manual Verification
1.  Open "模板与输入区设置".
2.  Click "添加新的输入区" (Add Field).
3.  Try to enter `123test` (Starts with number) -> Expect Warning.
4.  Try to enter `test-var` (Hyphen) -> Expect Warning.
5.  Try to enter `valid_var` -> Expect Success.
6.  Try to enter `合法变量` (Chinese) -> Expect Success (as it's valid in Python 3).
