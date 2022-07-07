"""
Tests correctness of base dataframe manipulation for detailed report generation
"""
from pandas import DataFrame
from numpy import nan

from babel.reports.reports import (
    create_total_items_by_branch_dataframe,
    create_lang_audn_mat_to_branch_dataframe,
)


def test_create_total_items_by_branch_dataframe(stub_dataframe):
    df = create_total_items_by_branch_dataframe(stub_dataframe)
    assert isinstance(df, DataFrame)
    assert list(df.columns) == ["code", "location", "copies"]
    assert df.iloc[[0]].values.tolist() == [["be", "Belmont", 2]]
    assert df.shape == (15, 3)


def test_create_lang_audn_mat_to_branch_dataframe(stub_dataframe):
    df = create_lang_audn_mat_to_branch_dataframe(stub_dataframe)
    assert isinstance(df, DataFrame)
    assert list(df.columns) == [
        "language",
        "audience",
        "mtype",
        "CL",
        "CN",
        "SB",
        "BE",
        "HK",
        "SG",
        "GC",
        "TH",
        "FT",
        "KP",
        "RS",
        "SN",
        "FX",
        "HG",
        "MH",
    ]
    # assert df.shape == (23, 18)
