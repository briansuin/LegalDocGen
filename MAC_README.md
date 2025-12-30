# LegalDocGen - macOS Build Instructions

Since you are moving the source code to a Mac, please follow these steps to build the application.

## 1. Prerequisites
Ensure you have Python 3 installed.
Open Terminal and navigate to the project folder.

**Critical Step**: Install macOS Developer Tools (required for PyInstaller):
```bash
xcode-select --install
```
(A dialog will appear. Click "Install" and wait for it to finish.)

Install the required libraries:
```bash
pip3 install PyQt6 docxtpl pyinstaller
```

## 2. Build the App
Run the provided build script:
```bash
python3 build_mac.py
```

This will:
1.  Clean up any old builds.
2.  Run PyInstaller with the correct settings for macOS (`--windowed`, hidden imports, etc.).
3.  Create a standalone application bundle.

## 3. Run the App
The application will be generated at:
`dist/LegalDocGen.app`

You can verify it by running:
```bash
open dist/LegalDocGen.app
```
Or simply double-click it in Finder.

## 4. Data Storage
On macOS, the generic "Installed" version of the app stores data (templates & config) in:
`~/Library/Application Support/LegalDocGen/`

-   **Templates**: Put your project folders here.
-   **Config**: JSON configuration files are stored here.


## 5. Troubleshooting / Common Issues

### "The application cannot be opened" (应用程序无法打开)
This generic error usually happens for two reasons when moving the app between computers:

#### A. Architecture Mismatch (Chip Type)
-   **Cause**: You compiled the app on an **Apple Silicon (M1/M2/M3)** Mac, but are trying to run it on an **Intel** Mac. (Or vice versa).
-   **Solution**: PyInstaller creates single-architecture builds by default.
    -   To run on Intel Macs, you must build it on an Intel Mac.
    -   To run on Apple Silicon, you must build it on an Apple Silicon Mac.
    -   (Tip: You can try running `arch -x86_64 python3 build_mac.py` on an M1 Mac to force an Intel build, but it requires an x86 Python environment).

#### B. Security / Gatekeeper (Quarantine)
-   **Cause**: macOS blocks unsigned apps transferred via AirDrop, Network, or Internet.
-   **Solution**: You must remove the "Quarantine" attribute.
    1.  Open Terminal.
    2.  Type `sudo xattr -cr ` (notice the space at the end).
    3.  Drag the `.app` file into the Terminal window.
    4.  Press Enter and type your password.
    
    Example:
    ```bash
    sudo xattr -cr /Path/To/LegalDocGen.app
    ```
