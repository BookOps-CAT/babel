# updates babel application

import shutil
import os
import sys
import time
import subprocess
from zipfile import ZipFile


def run_update(src_directory, dst_directory):
    if os.path.isfile('babel.exe'):

        CREATE_NO_WINDOW = 0x08000000

        # kill the app
        try:
            subprocess.call(
                'TASKKILL /F /IM babel.exe',
                creationflags=CREATE_NO_WINDOW)
            time.sleep(1)
        except:
            pass

        # delete content of the main folder except updater.exe
        entries = [f for f in os.listdir(dst_directory) if 'updater' not in f]
        for f in entries:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

        # unzip babel archive in default app location
        zipfile = os.path.join(src_directory, 'babel.zip')
        with ZipFile(zipfile, 'r') as zip:
            zip.extractall(dst_directory)

        subprocess.call(
            'babel.exe',
            creationflags=CREATE_NO_WINDOW)


if __name__ == '__main__':
    run_update(sys.argv[1], sys.argv[2])
