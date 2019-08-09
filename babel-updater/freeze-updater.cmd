REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --windowed ^
    --onefile ^
    --icon=updater.ico ^
    updater.py

