REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --windowed ^
    --onefile ^
    --icon=updater.ico ^
    --add-data="updater.png;." ^
    --hidden-import="win32timezone" ^
    --additional-hooks-dir=. ^
    babelsetup.py

