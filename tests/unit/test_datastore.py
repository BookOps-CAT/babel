from sqlalchemy.engine.url import URL
from babel.data.datastore import datastore_url, DataAccessLayer
from babel.paths import get_user_data_handle


def test_datastore_url(mock_vault, dummy_user_data):
    result = datastore_url(dummy_user_data)

    assert isinstance(result, URL)
    assert (
        str(result)
        == "mysql+pymysql://test:babel_key@localhost:3306/babeltest?charset=utf8"
    )


def test_DataAccessLayer(mock_vault, dummy_user_data):
    dal = DataAccessLayer()
    assert (
        str(dal.db_url)
        == "mysql+pymysql://test:babel_key@localhost:3306/babeltest?charset=utf8"
    )
