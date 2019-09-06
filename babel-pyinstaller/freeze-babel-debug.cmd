REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --debug=imports ^
    --onedir ^
    --additional-hooks-dir=. ^
    --hidden-import="win32timezone" ^
    --hidden-import="pymysql" ^
    --hidden-import="sqlalchemy.ext.baked" ^
    --icon=".\icons\babel2.ico" ^
    --add-data="./icons;icons" ^
    --add-data="version.txt;." ^
    --version-file=win_info.txt ^
    babel.py
