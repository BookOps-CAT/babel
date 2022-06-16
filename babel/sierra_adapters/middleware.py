"""
This modules handles calls to particular Sierra middleware to discover
any duplicates in the ILS.
"""
import os
import logging
from requests import Response
import shelve
from typing import Optional, Union


from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformToken, PlatformSession
from bookops_nypl_platform.errors import BookopsPlatformError


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


def catalog_match(
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


def catalog_lookup(middleware: Union[PlatformSession, SolrSession], sierra_number: str):
    """
    Looks up bibliographic and item data in Sierra.
    Makes two requests: first to obtain bib data then second to obtain its items data

    Args:
        middleware:                 `NypPlatform` or `BplSolr` instance
        sierra_number:              Sierra bib number, 8 digits without b prefix

    Returns:

    """
    pass


class NypPlatform(PlatformSession):
    def __init__(self, library: str, creds_fh: str) -> None:
        """
        Authenticates and opens a session with NYPL Platform.
        Relies on credentials stores in Windows Credential Manager.

        Args:
                library:            'branches' or 'research'
                creds_fh:           path to user_data `shelve.BsdDbShelf` instance
        """
        mlogger.info("Initiating session with Platform.")

        self.library = library  # branches or research
        self.creds_fh = creds_fh

        if self.library not in ("branches", "research", None):
            mlogger.error(
                "Invalid library argument passed to NypPlatform. Unable to open Platfrom session."
            )
            raise BabelError("Invalid library argument passed.")

        if not os.path.exists(f"{self.creds_fh}.dat"):
            mlogger.error("Invalid creds_fh argument passed.")
            raise BabelError(
                "Path to user_data not provided. Unable to open Platform session."
            )

        self.agent = "BookOps/Babel"

        token = self._get_token()

        super().__init__(authorization=token, agent=self.agent)

    def _get_credentials(
        self, user_data: shelve.BsdDbShelf
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Retrieves NYPL Platform credentials from user_data and vault"""

        mlogger.debug("Obtaining Platform credentials.")
        try:
            config = user_data["nyp_platform"]
            client_id = config["PLATFORM_CLIENT_ID"]
            oauth_server = config["PLATFORM_OAUTH_SERVER"]
            mlogger.debug("Found Platform credentials in user_data.")
        except KeyError:
            mlogger.error("Failed to find Platform credentials in user_data.")
            client_id = None
            oauth_server = None

        client_secret = get_from_vault("babel_platform", client_id)

        return client_id, client_secret, oauth_server

    def _get_token(self) -> Optional[PlatformToken]:
        """Obtains NYPL Platform access token"""

        mlogger.debug("Obtaining Platform access token.")

        # check if valid token still available
        # if not request new one
        user_data = shelve.open(self.creds_fh)

        try:
            token = user_data["platform_token"]
            mlogger.debug("Found Platform access token in user_data.")
        except KeyError:
            mlogger.debug("Failed to find access token in user_data.")
            token = None

        if not token or token.is_expired():

            mlogger.info("Requesting new Platform access token.")
            client_id, client_secret, oauth_server = self._get_credentials(user_data)
            token = PlatformToken(client_id, client_secret, oauth_server, self.agent)

        user_data.close()
        return token

    def _get_bib_nos(self, response: Response) -> list[str]:
        """
        Parses Platform response and provides list of Sierra bib numbers of the
        matches.

        Args:
            response:               `requests.Response` object

        Returns:
            bib_nos:                list of bib numbers as strings
        """
        return [bib["id"] for bib in response.json()["data"]]

    def _is_library_match(self, is_research: bool) -> bool:
        """
        Determines if cart library matches library on matching Platform bib

        Args:
            is_research:            Platform's `is_research` bib field value

        Returns:
            bool
        """

        if self.library is None:
            return True
        elif self.library == "research" and is_research:
            return True
        elif self.library == "branches" and not is_research:
            return True
        else:
            return False

    def _determine_library_matches(self, bib_nos: list[str]) -> list[str]:
        """
        Performs a search to determine if bib on the provided list
        matches proper NYPL library (branches or research).

        Args:
            bib_nos:                list of Sierra bib numbers as strings

        Returns:
            library_bib_nos
        """
        matches = []

        for bib_no in bib_nos:
            response = self.check_bib_is_research(id=bib_no)
            if response.status_code == 200 and self._is_library_match(
                response.json()["isResearch"]
            ):
                matches.append(bib_no)

        return matches

    def search(self, keywords: list[str]) -> tuple[bool, str]:
        """
        Searches NYPL Platform for given ISBNs or UPCs.

        Args:
            keywords:               list or comma separated string of ISBNs
                                    or UPCs to search Sierra

        Returns:
            catalog_dup & dup_bibs
        """
        try:
            response = self.search_standardNos(keywords=keywords, deleted=False)
            if response.status_code == 200:
                bib_nos = self._get_bib_nos(response)
                library_matches = self._determine_library_matches(bib_nos)
                if library_matches:
                    catalog_dup = True
                    dup_bibs = ",".join(library_matches)
                else:
                    catalog_dup = False
                    dup_bibs = None
            else:
                catalog_dup = False
                dup_bibs = None
        except BookopsPlatformError:
            mlogger.warning("Encountered problem with Platform request. Skipping.")
            catalog_dup = None
            dup_bibs = None

        return catalog_dup, dup_bibs

    def _store_token(self):
        if isinstance(self.authorization, PlatformToken):
            user_data = shelve.open(self.creds_fh)
            user_data["platform_token"] = self.authorization
            user_data.close()

    def close(self):
        # store token for future use before closing the session
        self._store_token()
        for v in self.adapters.values():
            v.close()


class BplSolr(SolrSession):
    def __init__(self):
        pass
