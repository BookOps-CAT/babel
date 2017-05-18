# updates Babel as frozen binaries
import shutil
import os
import sys
import time


def run_update(directory):
    if os.path.isfile('babel.exe'):
        os.system("TASKKILL /F /IM babel.exe")
        time.sleep(1)
        os.remove('babel.exe')
        shutil.copy2(directory + 'babel.exe', 'babel.exe')
        # relaunch babel
        os.system('babel.exe')

if __name__ == '__main__':
    run_update(sys.argv[1])
