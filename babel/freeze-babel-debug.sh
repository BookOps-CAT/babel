# Babel Pyinstaller command to produce Windows executable files
clear
pyinstaller --clean --debug=imports \
	--paths="." \
	--onedir \
	--icon="./icons/babel2.ico" \
    --add-data="./icons;icons" \
    --add-data="creds.bin;." \
    --version-file=win_info.txt \
    babel.py
