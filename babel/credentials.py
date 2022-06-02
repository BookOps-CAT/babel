"""
Module handling initial ingests of services credentials to
Windows Credential Manager and managing their retrieval
"""
import binascii
import os.path
import shelve
from typing import Union


from cryptography.fernet import Fernet, InvalidToken
import keyring
from keyring.errors import PasswordDeleteError, PasswordSetError

try:
    from errors import BabelError
except ImportError:
    # for pytest imports
    from .errors import BabelError


def encrypt_file_data(key: bytes, src_fh: str, dst_fh: str) -> None:
    """
    Encrypts data from a source file.

    Args:
        key:            a secret key as bytes
        src_fh:         a path of the file to be encrypted
        dst_fh:         a destination path of the encrypted file
    """
    with open(src_fh, "rb") as src:
        src_data = src.read()
        f = Fernet(key)
        encrypted_data = f.encrypt(src_data)

    with open(dst_fh, "wb") as dst:
        dst.write(encrypted_data)


def decrypt_file_data(key: Union[str, bytes], fh: str) -> bytes:
    """
    Decrypts encoded data in a file.

    Args:
        key:            a secret key as bytes
        fh:             file path of the source file

    Returns:
        decrypted data as bytes
    """
    try:
        f = Fernet(key)
        with open(fh, "rb") as src:
            data = src.read()
            decrypted_data = f.decrypt(data)

        return decrypted_data
    except FileNotFoundError:
        raise BabelError("Unable to locate 'creds.bin' file.")
    except (binascii.Error, InvalidToken):
        raise BabelError("Invalid secret key provided.")


def generate_key() -> bytes:
    """
    Creates a secret key to be used to encode data.

    Returns:
        secret key as bytes
    """
    return Fernet.generate_key()


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
