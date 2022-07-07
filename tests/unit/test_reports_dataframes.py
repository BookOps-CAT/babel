"""
Tests correctness of base dataframe manipulation for detailed report generation
"""
from pandas import DataFrame

from babel.reports.reports import create_total_items_by_branch_dataframe


def test_create_total_items_by_branch_dataframe(stub_dataframe):
    df = create_total_items_by_branch_dataframe(stub_dataframe)
    assert isinstance(df, DataFrame)
    assert list(df.columns) == ["code", "location", "copies"]
    assert df.iloc[[0]].values.tolist() == [["be", "Belmont", 2]]
    assert df.shape == (15, 3)
