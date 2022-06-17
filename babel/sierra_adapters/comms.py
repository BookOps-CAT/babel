"""
Higher level, unified methods to communicate with NYPL Platform & BPL Solr
"""
from typing import Union

from bookops_nypl_platform import PlatformSession
from bookops_bpl_solr import SolrSession


def catalog_lookup(middleware: Union[PlatformSession, SolrSession], sierra_number: str):
    """
    Looks up bibliographic and item data in Sierra.
    Makes two requests: first to obtain bib data then second to obtain its items data

    Args:
        middleware:                 `NypPlatform` or `BplSolr` instance
        sierra_number:              Sierra bib number, 8 digits without b prefix

    Returns:

    """
    bib_data, item_data = middleware.get_bib_and_item_data(sierra_number)
    return bib_data, item_data


def catalog_dup_search(
    middleware: Union[PlatformSession, SolrSession], keywords: list[str]
) -> tuple[bool, str]:
    """
    Performs a search in given middleware for given keywords (ISBN, UPC)

    Args:
        middleware:                 `NypPlatform` or `BplSolr` instance
        keywords:                   list of ISBNs or UPC to search middleware

    Returns:
        bool, bib#s as comma separated string
    """
    catalog_dup, dup_bibs = middleware.search(keywords)

    return catalog_dup, dup_bibs
