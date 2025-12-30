@echo off
echo Installing PyInstaller...
python -m pip install pyinstaller

echo Cleaning up previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Building Executable...
python -m PyInstaller --noconsole --name "LegalDocGen" --icon=NONE --clean --add-data "src;src" main.py

echo Copying templates to _internal...
if not exist "dist\LegalDocGen\_internal\templates" mkdir "dist\LegalDocGen\_internal\templates"
xcopy templates "dist\LegalDocGen\_internal\templates" /E /I /Y

echo Build Complete! Check the 'dist' folder.
pause
