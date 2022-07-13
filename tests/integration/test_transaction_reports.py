from pandas import DataFrame

from babel.data.transactions_reports import query2dataframe


def test_query2dataframe(dev_user_data, mock_db_creds_from_vault):
    result = query2dataframe(None, None, [], "2022-04-01", "2022-06-30")
    assert isinstance(result, DataFrame)
