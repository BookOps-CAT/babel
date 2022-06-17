from babel.sierra_adapters.comms import catalog_lookup, catalog_dup_search


def test_catalog_lookup_platform(
    mock_platform,
    mock_platform_get_bib_success,
    mock_platform_get_items_success,
):
    result = catalog_lookup(mock_platform, "21742979")
    assert isinstance(result, tuple)
    assert isinstance(result[0], dict)
    assert isinstance(result[1], list)


def test_catalog_search_platform(
    mock_platform,
    mock_platform_determine_library_matches,
    mock_platform_session_get_list_response_200http,
):
    result = catalog_dup_search(mock_platform, ["isbn", "upc"])
    assert isinstance(result, tuple)
    assert result[0] is True
    assert result[1] == "21742979"
