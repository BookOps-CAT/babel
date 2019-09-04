# updates babel application

from distutils.dir_util import copy_tree
import logging
import logging.config
import os
import psutil
import shutil
import sys
import time


def run_update(src_directory, dst_directory):

    # set up logging
    LOG_FILE = 'updater_log.out'
    ulogger = logging.getLogger('updater_logger')
    ulogger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)-15s: %(levelname)-8s %(message)s')
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1024 * 1024, backupCount=5)
    handler.setFormatter(formatter)
    ulogger.addHandler(handler)

    ulogger.info('Initiating update...')
    ulogger.debug(
        f'Update source: {src_directory}, destination: {dst_directory}')

    untouchables = []
    if os.path.isfile(os.path.join(dst_directory, 'babel.exe')):
        ulogger.debug('Located succesfully Babel2 directory.')

        # kill the babel app
        try:
            ulogger.debug('CWD: {}'.format(os.getcwd()))
            # subprocess.run(
            #     'TASKKILL /F /T /IM babel.exe',
            #     creationflags=subprocess.CREATE_NO_WINDOW)
            killed = False
            for proc in psutil.process_iter():
                if proc.name() == 'babel.exe':
                    proc.kill()
                    killed = True
                    ulogger.debug('Process babel.exe has been killed.')
            if not killed:
                ulogger.error('Unable to find & kill babel.exe process.')

            time.sleep(1)

        except Exception as e:
            ulogger.error('Unable to kill babel.exe. Error: {}'.format(e))

        ulogger.info('Removing old files...')
        # delete content of the main folder except updater.exe
        entries = [
            f for f in os.listdir(dst_directory) if 'updater' not in f]

        for f in entries:
            if os.path.isdir(os.path.join(dst_directory, f)):
                shutil.rmtree(os.path.join(dst_directory, f))
                ulogger.debug(
                    'Deleted directory: {}'.format(
                        os.path.join(dst_directory, f)))
            elif os.path.isfile(os.path.join(dst_directory, f)):
                try:
                    os.remove(os.path.join(dst_directory, f))
                    ulogger.debug(
                        'Deleted file: {}'.format(
                            os.path.join(dst_directory, f)))
                except FileNotFoundError:
                    ulogger.error(
                        'Unable to find file: {}'.format(
                            os.path.join(dst_directory, f)))
                except PermissionError:
                    untouchables.append(f)
                    ulogger.debug(f'PermissionError on {f}')
                except WindowsError:
                    untouchables.append(f)
                    ulogger.debug(f'WindowsError on {f}')
            else:
                print('Unrecognized entry: {}'.format(
                    os.path.join(dst_directory, f)))

        time.sleep(2)

        ulogger.info(f'Found following untouchable files: {untouchables}')

        ulogger.debug('Copying new files')
        # copy updated files
        entries = [
            f for f in os.listdir(src_directory) if 'updater' not in f]
        for f in entries:
            try:
                if f not in untouchables:
                    if os.path.isdir(os.path.join(src_directory, f)):
                        copy_tree(
                            os.path.join(src_directory, f),
                            os.path.join(dst_directory, f))
                        ulogger.debug(
                            'Copied directory: {}'.format(
                                os.path.join(dst_directory, f)))
                    elif os.path.isfile(os.path.join(src_directory, f)):
                        shutil.copy2(
                            os.path.join(src_directory, f), dst_directory)
                        ulogger.debug(
                            'Copied file: {}'.format(
                                os.path.join(dst_directory, f)))
                    else:
                        ulogger.error(f'Unable to copy entry: {f}')
                else:
                    ulogger.debug(f'Skipping untouchable file {f}')
            except PermissionError:
                ulogger.error(f'PermissionError on {f}')

        ulogger.info('Copying complete...')
        time.sleep(1)
        ulogger.debug(f'CWD: {os.getcwd()}')
        os.startfile('babel.exe')
        ulogger.info('Complete. Launching Babel...')

    else:
        ulogger.error('Unable to locate Babel2 main directory.')


if __name__ == '__main__':
    run_update(sys.argv[1], sys.argv[2])
