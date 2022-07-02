"""
This module handles requests to BPL Solr.
"""
import os
import json
import logging
import shelve
from typing import Optional

from bookops_bpl_solr import SolrSession
from bookops_bpl_solr.session import BookopsSolrError
from requests import Response

try:
    from credentials import get_from_vault
    from logging_settings import LogglyAdapter
    from errors import BabelError
except ImportError:
    # tests
    from babel.credentials import get_from_vault
    from babel.errors import BabelError
    from babel.logging_settings import LogglyAdapter


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


class BplSolr(SolrSession):
    def __init__(self, creds_fh: str) -> None:
        """
        Creates a session with BPL Solr.
        Relies on credentials stored in Windows Credential Manager.

        Args:
            creds_fh:               path to user_data `shelve.BsdDbSelf` instance
        """
        mlogger.info("Initiating session with BPL Solr.")

        self.creds_fh = creds_fh

        if not os.path.exists(f"{self.creds_fh}.dat"):
            mlogger.error("Invalid creds_fh argument passed.")
            raise BabelError(
                "Valid path to user_data not provided. Unable to open BPL Solr session."
            )

        endpoint, authorization = self._get_creds()

        super().__init__(
            authorization=authorization, endpoint=endpoint, agent="BookOps/Babel"
        )

    def _get_bib_nos(self, response: Response) -> list[str]:
        """
        Parses Solr response and returns matching Sierra bib #s.

        Args:
            response:               `requests.Response` instance

        Returns:
            bib_nos
        """
        return [bib["id"] for bib in response.json()["response"]["docs"]]

    def _get_creds(self) -> tuple[Optional[str], Optional[str]]:
        """
        Retrieves Solr secret key from Windows Credential Manager.

        Returns:
            endpoint, client-key
        """
        mlogger.debug("Obtaining Solr secret key.")

        user_data = shelve.open(self.creds_fh)

        try:
            endpoint = user_data["bpl_solr"]["SOLR_ENDPOINT"]
        except KeyError:
            mlogger.error("Failed to find BPL Solr endpoint in user_data.")
            endpoint = None
        finally:
            user_data.close()

        client_key = get_from_vault("babel_solr", "babel")
        if client_key is None:
            mlogger.error("Unable to obtain BPL Solr client-key from vault.")

        if not endpoint or not client_key:
            raise BabelError("Unable to obtain BPL Solr credentials.")
        else:
            return endpoint, client_key

    def _get_bib(self, sierra_number: str) -> Optional[dict]:
        """
        Makes a Solr request for particular Sierra record.

        Args:
            sierra_number:          Sierra 8-digit number

        Returns:
            response as dict
        """
        try:
            response = self.search_bibNo(
                sierra_number,
                default_response_fields=False,
                response_fields="id,title,author_raw,publisher,sm_item_data",
            )
        except BookopsSolrError:
            mlogger.warning(f"Unable to retrieve bib {sierra_number} data from Solr.")
            response = None

        if response and response.status_code == 200:
            return response.json()
        else:
            return None

    def _normalize_publisher(self, value: str) -> str:
        """
        Removes any 880 link tag from returned in Solr response

        Args:
            value:                  string

        Returns:
            norm_value
        """
        if value.startswith("880-"):
            return value[7:].strip()
        else:
            return value

    def _parse_bibliographic_data(self, response: dict) -> dict:
        """
        Parses Solr response for bibliographic data.

        Args:
            response:               Solr response as dict

        Returns:
            bibNo, author, title, pub data as dictionary
        """

        data = response["response"]["docs"][0]
        publisher = self._normalize_publisher(data["publisher"])
        return dict(
            bibNo=data["id"],
            title=data["title"],
            author=data["author_raw"],
            pubDate="",
            pubPlace=publisher,
        )

    def _parse_item_data(self, response: dict) -> dict:
        """
        Parses Solr response for item data

        Args:
            response:               Solr response as dict

        Returns:
            list of dict with locCode, LocName, status, circ, lastCheck
        """
        data = response["response"]["docs"][0]

        items = []

        try:
            for item_str in data["sm_item_data"]:
                item = json.loads(item_str)
                items.append(
                    dict(
                        locCode=item["location"]["code"],
                        locName=item["location"]["name"],
                        status=item["status"]["display"],
                        circ="n/a",
                        lastCheck="n/a",
                    )
                )
        except KeyError:
            # order record only, no items
            pass

        return items

    def get_bib_and_item_data(
        self, sierra_number: str
    ) -> tuple[Optional[dict], Optional[dict]]:
        """
        Retrieves from BPL Solr bib bibliographic and item data.

        Args:
            sierra_number:          sierra 8-digit bib number

        Returns:
            tuple of two dictionaries (bib_data, item_data)
        """
        response = self._get_bib(sierra_number)
        if response:
            bib_data = self._parse_bibliographic_data(response)
        else:
            bib_data = None

        if response:
            item_data = self._parse_item_data(response)
        else:
            item_data = None

        return bib_data, item_data

    def search(self, keywords: list[str], keyword_type: Optional[str] = "isbn"):
        """
        Searches BPL Solr for given ISBN or UPC.

        Args:
            keywords:               list of ISBNs or UPCs
            keyword_type:           'isbn' or "upc"

        Returns:
            catalog_dup & dup_bibs
        """
        try:
            if keyword_type == "isbn":
                response = self.search_isbns(
                    keywords,
                    default_response_fields=False,
                    response_fields="id",
                )
            elif keyword_type == "upc":
                response = self.search_upc(
                    keywords, default_response_fields=False, response_fields="id"
                )
            else:
                mlogger.warning(
                    "Attempting unsupported search in BPL Solr. Only ISBN and UPC searches are permitted."
                )
                response = None
                catalog_dup = False
                dup_bibs = None

            if response and response.status_code == 200:
                bib_nos = self._get_bib_nos(response)
                if bib_nos:
                    catalog_dup = True
                    dup_bibs = ",".join(bib_nos)
                else:
                    catalog_dup = False
                    dup_bibs = None
            else:
                catalog_dup = False
                dup_bibs = None
        except BookopsSolrError:
            mlogger.warning("Encountered problem with Solr request. Skipping.")
            catalog_dup = False
            dup_bibs = None

        return catalog_dup, dup_bibs
