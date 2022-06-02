import os

from cryptography.fernet import Fernet
import keyring
import pytest


from babel.credentials import (
    encrypt_file_data,
    decrypt_file_data,
    generate_key,
    get_from_vault,
    store_in_vault,
)
from babel.errors import BabelError


def test_generate_key():
    key = generate_key()
    assert isinstance(key, bytes)


def test_encrypt_file_data(tmpdir):
    # setup
    key = Fernet.generate_key()
    src_fh = os.path.join(tmpdir, "src.txt")
    with open(src_fh, "wb") as f:
        f.write(b"spam")
    dst_fh = os.path.join(tmpdir, "dst.bin")

    # execute
    encrypt_file_data(key, src_fh, dst_fh)

    # verify
    assert os.path.exists(dst_fh)
    with open(dst_fh, "rb") as dst:
        data = dst.read()

        f = Fernet(key)
        assert f.decrypt(data) == b"spam"


def test_decrypt_file_data(tmpdir):
    key = Fernet.generate_key()
    f = Fernet(key)
    fh = os.path.join(tmpdir, "src.bin")
    with open(fh, "wb") as src:
        src.write(f.encrypt(b"spam"))

    assert decrypt_file_data(key, fh) == b"spam"


def test_decrypt_file_data_file_not_found():
    key = Fernet.generate_key()
    fh = ""

    with pytest.raises(BabelError) as exc:
        decrypt_file_data(key, fh)

    assert "Unable to locate 'creds.bin' file." in str(exc.value)


@pytest.mark.parametrize("arg", ["foo", "JPJxKI-lCp9NVkm4NyhZGyBDnGakjsIFv9E1z0X-8s4="])
def test_decrypt_file_data_invalid_key(tmpdir, arg):
    key = Fernet.generate_key()
    f = Fernet(key)
    fh = os.path.join(tmpdir, "src.bin")
    with open(fh, "wb") as src:
        src.write(f.encrypt(b"spam"))

    with pytest.raises(BabelError) as exc:
        decrypt_file_data(arg, fh)

    assert "Invalid secret key provided." in str(exc.value)


def test_store_in_vault():
    app = "test_app"
    user = "test_user"
    passw = "test_passw"
    store_in_vault(app, user, passw)

    assert passw == keyring.get_password(app, user)

    # clean up
    keyring.delete_password(app, user)


def test_get_from_vault():
    app = "test_app"
    user = "test_user"
    passw = "test_passw"
    keyring.set_password(app, user, passw)

    assert passw == get_from_vault(app, user)

    keyring.delete_password(app, user)
