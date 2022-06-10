from contextlib import nullcontext as does_not_raise

import pytest

from babel.sierra_adapters.middleware import NypPlatform


@pytest.mark.parametrize("arg", [None, "branch", "research"])
def test_NypPlatform_valid_library_arg(arg, mock_vault):
    with does_not_raise():
        session = NypPlatform(arg)


@pytest.mark.parametrize("arg", ["", "foo", 1])
def test_NypPlatform_invalid_library_arg(arg, mock_vault):
    with pytest.raises(ValueError) as exc:
        NypPlatform(arg)

    assert "Invalid library argument passed" in str(exc.value)


def test_NypPlatform_get_credentials(mock_user_data):
    pass
