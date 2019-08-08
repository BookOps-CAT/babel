REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --clean --debug=imports ^
    --onedir ^
    --additional-hooks-dir=. ^
    --hidden-import="win32timezone" ^
    --hidden-import="pymysql" ^
    --icon=".\icons\babel.ico" ^
    --add-data="./icons;icons" ^
    --add-data="version.txt;."
    babel.py
