REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --windowed ^
    --hidden-import="win32timezone" ^
    --onefile ^
    --icon=updater.ico ^
    updater.py
