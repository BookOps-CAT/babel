REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --windowed ^
    --onedir ^
    --hidden-import="win32timezone" ^
    --hidden-import="pymysql" ^
    --hidden-import="sqlalchemy.ext.baked" ^
    --icon=".\icons\babel2.ico" ^
    --add-data="./icons;icons" ^
    --add-data="version.txt;." ^
    --add-data="creds.bin;." ^
    --version-file=win_info.txt ^
    babel.py
