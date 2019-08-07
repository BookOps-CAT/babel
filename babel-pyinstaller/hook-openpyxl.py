# hook-openpyxl.py
# run pyinstaller as follows: pyinstaller.exe --additional-hooks-dir=. yourscriptname.py

from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ['pymysql']

datas = collect_data_files('openpyxl')
datas += collect_data_files('pymysql')
