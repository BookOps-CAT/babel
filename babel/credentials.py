"""
Module handling initial ingests of services credentials to
Windows Credential Manager and managing their retrieval
"""

from Crypto.Cipher import AES
import keyring
from keyring.errors import PasswordDeleteError, PasswordSetError
import os.path
import shelve

from errors import BabelError


def locate_credentials(shelf_fh, creds_fh):
    """
    creates a path to folder where credentials are
    stored
    returns:
        path: string, path to credentials.bin
    """

    user_data = shelve.open(shelf_fh)
    try:
        update_dir = user_data['paths']['update_dir']
        if update_dir == '':
            return None
        else:
            creds_path = os.path.join(
                os.path.split(update_dir)[0], creds_fh)
            return creds_path
    except KeyError:
        return None
    finally:
        user_data.close()


def encrypt_file_data(key, source, dst):
    """
    encrypts data in a file
    args:
        key: string, 16-bit encryption key
        source: string, path to file to be encrypted
        dst: string, path to encrypted file
    """

    cipher = AES.new(key, AES.MODE_EAX)
    with open(source, 'rb') as file:
        data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(data)
        file_out = open(dst, 'wb')
        [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]


def decrypt_file_data(key, fh):
    """
    decrypts data in a file
    args:
        key: string,  16-bit encryption key
        fh: string, file handle of file to be decrypted
    returns:
        data: string
    """
    try:
        with open(fh, 'rb') as file:
            nonce, tag, ciphertext = [file.read(x) for x in (16, 16, -1)]
            cipher = AES.new(key, AES.MODE_EAX, nonce)
            data = cipher.decrypt_and_verify(ciphertext, tag)
            return data
    except ValueError as e:
        raise BabelError(e)


def get_from_vault(application, user):
    """
    gets password for appliction/user from Windows Credential Locker
    args:
        application: string, name of applicaiton
        user: string, name of user
    returns:
        password: string
    """

    password = keyring.get_password(application, user)
    return password


def store_in_vault(application, user, password):
    """
    stores credentials in Windows Credential Locker
    args:
        applicaiton: string,  name of application
        user: string, name of user
        password: string
    """

    # check if credentials already stored and if so
    # delete and store updated ones
    try:
        if not get_from_vault(application, user):
            keyring.set_password(application, user, password)
        else:
            keyring.delete_password(application, user)
            keyring.set_password(application, user, password)
    except PasswordSetError as e:
        raise BabelError(e)
    except PasswordDeleteError as e:
        raise BabelError(e)


def delete_from_vault(application, user):
    try:
        keyring.delete_password(application, user)
    except PasswordDeleteError:
        pass
