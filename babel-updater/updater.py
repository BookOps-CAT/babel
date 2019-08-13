# updates babel application

import shutil
import os
import sys
import time
import subprocess
from zipfile import ZipFile


def run_update(src_directory, dst_directory):
    if os.path.isfile(os.path.join(dst_directory, 'babel.exe')):

        # kill the babel app
        try:
            subprocess.run(
                'TASKKILL /F /T /IM babel.exe',
                creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(5)
        except:
            pass

        # delete content of the main folder except updater.exe
        entries = [f for f in os.listdir(dst_directory) if 'updater.exe' not in f]
        for f in entries:
            if os.path.isdir(os.path.join(dst_directory, f)):
                shutil.rmtree(os.path.join(dst_directory, f))
            else:
                try:
                    os.remove(os.path.join(dst_directory, f))
                except FileNotFoundError:
                    pass
                except PermissionError as e:
                    pass

        # unzip babel archive in default app location
        zipfile = os.path.join(src_directory, 'babel2.zip')
        with ZipFile(zipfile, 'r') as zip:
            zip.extractall(dst_directory)

        print('Extracted')

        os.startfile(os.path.join(dst_directory, 'babel.exe'))


if __name__ == '__main__':
    run_update(sys.argv[1], sys.argv[2])