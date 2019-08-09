REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --windowed ^
    --onedir ^
    --additional-hooks-dir=. ^
    --hidden-import="win32timezone" ^
    --hidden-import="pymysql" ^
    --icon=".\icons\babel2.ico" ^
    --add-data="./icons;icons" ^
    --add-data="version.txt;." ^
    --version-file=win_info.txt ^
    babel.py
