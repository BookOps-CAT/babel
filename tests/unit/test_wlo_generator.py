# -*- coding: utf-8 -*-

import pytest

from babel.data.wlo_generator import wlo_pool


@pytest.mark.parametrize(
    "arg1,arg2,expectation",
    [
        (None, 1, ["wlo0000000001"]),
        ("wlo0000000100", 1, ["wlo0000000101"]),
        (
            "wlo1000000007",
            5,
            [
                "wlo1000000008",
                "wlo1000000009",
                "wlo1000000010",
                "wlo1000000011",
                "wlo1000000012",
            ],
        ),
    ],
)
def test_wlo_pool(arg1, arg2, expectation):
    pool = [w for w in wlo_pool(arg1, arg2)]
    assert pool == expectation


@pytest.mark.parametrize("arg", ["wlo1", "wlo99999999991"])
def test_wlo_pool_invalid_wlo_exception(arg):
    with pytest.raises(ValueError) as exc:
        next(wlo_pool(arg, 1))
    assert str(exc.value) == "invalid wlo number passed"


def test_wlo_pool_too_large_exception():
    with pytest.raises(RuntimeError):
        next(wlo_pool("wlo9999999999", 1))
