# updates Babel as frozen binaries
import shutil
import os
import sys
import time
import shelve


def run_update(directory, update_version):
    if os.path.isfile('babel.exe'):
        os.system("TASKKILL /F /IM babel.exe")
        time.sleep(1)
        os.remove('babel.exe')
        shutil.copy2(directory + 'babel.exe', 'babel.exe')
        # update version info & relaunch babel
        user_data = shelve.open('user_data')
        user_data['version'] = update_version
        user_data.close()
        os.system('babel.exe')


if __name__ == '__main__':
    run_update(sys.argv[1], sys.argv[2])
