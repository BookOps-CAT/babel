REM Babel Pyinstaller command to produce Windows executable files
pyinstaller --onedir ^
    --windowed --clean ^
    --additional-hooks-dir=. ^
    --icon=".\icons\babel.ico" ^
    --add-data="./icons;icons" ^
    babel.py
