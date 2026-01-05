# Build Instructions

## 1. Build the Executable (Folder)
To create the standalone folder containing the executable:

1.  Open a terminal in the project directory (`d:\ProgramingProjects\LegalDocGen`).
2.  Run the build script:
    ```cmd
    .\build.bat
    ```
3.  Wait for the process to complete.
4.  The output will be in `dist\LegalDocGen`. You can run `LegalDocGen.exe` from inside that folder.

## 2. Create the Installer (Optional)
If you want a single file installer (setup.exe):

1.  Ensure you have **Inno Setup Compiler** installed.
2.  Double-click `setup_script.iss` to open it in Inno Setup.
3.  Click **Build** -> **Compile** (or press Ctrl+F9).
4.  The installer `LegalDocGen_Setup.exe` will be created in the `Output` folder (or next to the script, depending on settings).
