"""
Tests correctness of base dataframe manipulation for detailed report generation
"""
from pandas import DataFrame
from numpy import nan

from babel.reports.reports import (
    create_total_items_by_branch_dataframe,
    create_branch_to_lang_audn_mat_dataframe,
    create_lang_audn_mat_to_branch_dataframe,
    generate_basic_stats,
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

    # make sure rows and columns are sorted in alphabetical order
    assert df["language"].values.tolist() == [
        "Arabic",
        "Arabic",
        "Italian",
        "Italian",
        "Japanese",
        "Japanese",
        "Spanish",
    ]
    assert list(df.columns) == [
        "language",
        "audience",
        "mtype",
        "BE",
        "CL",
        "CN",
        "FT",
        "FX",
        "GC",
        "HG",
        "HK",
        "KP",
        "MH",
        "RS",
        "SB",
        "SG",
        "SN",
        "TH",
    ]
    assert df.iloc[[0]].values.tolist()[0][5] == 2.0
    assert df.shape == (7, 18)


def test_branch_to_lang_audn_mat_dataframe(stub_dataframe):
    df = create_branch_to_lang_audn_mat_dataframe(stub_dataframe)
    assert isinstance(df, DataFrame)
    assert df.shape == (15, 8)
    assert list(df.columns) == [
        "location",
        "Arabic juvenile print",
        "Arabic young adult print",
        "Italian juvenile print",
        "Italian young adult print",
        "Japanese adult print",
        "Japanese young adult print",
        "Spanish adult print",
    ]


def test_generate_basic_stats(stub_dataframe):
    data = generate_basic_stats(stub_dataframe, "2022-07-01", "2022-09-30")
    assert sorted(data.keys()) == [
        "babel_langs",
        "babel_mats",
        "bpl_langs",
        "bpl_mats",
        "end_date",
        "nypl_langs",
        "nypl_mats",
        "start_date",
        "total_items",
        "total_orders",
    ]
    assert isinstance(data["start_date"], str)
    assert isinstance(data["end_date"], str)
    assert isinstance(data["babel_langs"], DataFrame)
    assert isinstance(data["babel_mats"], DataFrame)
    assert isinstance(data["bpl_langs"], DataFrame)
    assert isinstance(data["bpl_mats"], DataFrame)
    assert isinstance(data["nypl_langs"], DataFrame)
    assert isinstance(data["nypl_mats"], DataFrame)
    assert isinstance(data["total_items"], DataFrame)
    assert isinstance(data["total_orders"], DataFrame)
