# Babel Pyinstaller command to produce Windows executable files
clear
pyinstaller --clean \
    --paths="." \
    --onedir \
    --windowed \
    --icon="./icons/babel2.ico" \
    --add-data="./icons;icons" \
    --add-data="creds.bin;." \
    --version-file=win_info.txt \
    babel.py
