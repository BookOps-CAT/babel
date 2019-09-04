REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --console ^
    --debug=imports ^
    --hidden-import="win32timezone" ^
    --onefile ^
    --icon=updater.ico ^
    --version-file=version.txt ^
    updater.py
