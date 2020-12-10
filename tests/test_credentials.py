from babel.credentials import get_from_vault, store_in_vault


import keyring


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
