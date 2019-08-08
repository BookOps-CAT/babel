from ftplib import FTP, all_errors
import os
import requests
import shutil
import sys
from zipfile import ZipFile

p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, p + '\\' + p.split('\\')[-1])
sys.path.insert(0, p)


from babel import paths
from babel.errors import BabelError


def create_space(temp_dir):

    try:
        # clean up previous installations
        shutil.rmtree(paths.APP_DATA_DIR)
        shutil.rmtree(paths.APP_DIR)
        shutil.rmtree(temp_dir)

        # recreate
        os.mkdir(paths.APP_DATA_DIR)
        os.mkdir(paths.PROD_LOG_PATH)
        os.mkdir(paths.APP_DIR)
        os.mkdir(temp_dir)

    except FileNotFoundError:
        pass

    except PermissionError as e:
        raise BabelError(e)


def connect2ftp(host, user, password):
    try:
        ftp = FTP(host)
        conn = ftp.login(user, password)
        if conn[:3] == '230':
            return ftp
        else:
            raise BabelError(
                f'Unable to connect to FTP. Server response: {conn}')
    except all_errors as e:
        raise BabelError(
            f'Unable to connect to FTP. Error: {e}')


def disconnect_ftp(ftp):
    try:
        ftp.quit()
    except all_errors:
        pass


def move2temp(ftp, fh, dstfh):
    try:
        # if transfer_type == 'binary':
        with open(dstfh, 'wb') as f:
            ftp.retrbinary('RETR %s' % fh, lambda data: f.write(data))
        # elif transfer_type == 'ASCII':
        #     with open(dstfh, 'w') as f:
        #         ftp.retrlines('RETR %s' % fh, lambda data: f.write(data))

    except all_errors as e:
        raise BabelError(
            f'Unable to download Babel files. Error: {e}')


def unpack(zipfile, temp_dir):
    with ZipFile(zipfile, 'r') as zip:
        # printing all the contents of the zip file
        # zip.printdir()

        # extracting all the files
        # print('Extracting all the files now...')
        try:
            shutil.rmtree(os.path.join(temp_dir))
        except FileNotFoundError:
            pass
        except PermissionError:
            # display msg
            raise
        os.mkdir(temp_dir)
        zip.extractall(temp_dir)
        # print('Done!')


def download_app(host, user, password, folder, zip_name, dst_fh):
    # ftp = connect2ftp(host, user, password)
    # ftp.cwd(folder)
    # move2temp(ftp, zip_name, dst_fh)
    # # unpack()
    # disconnect_ftp(ftp)

    # r = requests.get(url, stream=True)
    # with open(dst_fh, 'wb') as fd:
    #     c = 0
    #     for chunk in r.iter_content(chunk_size=524):
    #         c += 1
    #         print(f'downloading chunk {c}')
    #         fd.write(chunk)
    pass


if __name__ == '__main__':
    zip_name = 'babel2.zip'
    app_version = 'version.txt'
    folder = 'babel'
    host = [host]
    user = [user]
    passw =  [password]
    temp_zip_dir = os.path.join(os.environ['TEMP'], 'bookops-babel-temp')
    temp_zip_fh = os.path.join(temp_zip_dir, zip_name)
    temp_app_dir = os.path.join(temp_zip_dir, 'app')
    
    try:
        os.mkdir(temp_zip_dir)
    except FileExistsError:
        pass

    try:
        os.mkdir(temp_app_dir)
    except FileExistsError:
        pass

    download_app(host, user, passw, folder, zip_name, temp_zip_fh)


    # ftp = connect2ftp(host, user, passw)
    # disconnect_ftp(ftp)
