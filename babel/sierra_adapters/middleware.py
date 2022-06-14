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


def catalog_match(middleware: Union[PlatformSession, SolrSession], keywords: list[str]):
    catalog_dup = None
    dup_bibs = []

    catalog_dup, dup_bibs = middleware.search(keywords)

    return catalog_dup, dup_bibs


class NypPlatform(PlatformSession):
    def __init__(self, library: str, creds_fh: str) -> None:
        """
        Authenticates and opens a session with NYPL Platform.
        Relies on credentials stores in Windows Credential Manager.

        Args:
                library:            'branch' or 'research'
                creds_fh:           path to user_data `shelve.BsdDbShelf` instance
        """
        mlogger.info("Initiating session with Platform.")

        self.library = library  # branch or research
        self.creds_fh = creds_fh

        if self.library not in ("branch", "research", None):
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
        bib_nos = []
        data = response.json()["data"]
        for bib in data:
            bib_nos.append(bib["id"])

        return bib_nos

    def _find_library_matches(self, bib_nos: list[str]) -> list[str]:
        """
        Performs a search to determine if bib on the provided list
        matches library.

        Args:
            bib_nos:                list of Sierra bib numbers as strings

        Returns:
            library_bib_nos
        """
        matches = []
        if self.library is None:
            return matches
        else:
            for bib_no in bib_nos:
                try:
                    response = self.check_bib_is_research(id=bib_no)
                    if response.status_code == 200:
                        if (
                            self.library == "research"
                            and response.json()["is_research"]
                        ):
                            matches.append(bib_no)
                        elif (
                            self.library == "branch"
                            and not response.json()["is_research"]
                        ):
                            matches.append(bib_no)
                except BookopsPlatformError as exc:
                    pass
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
                library_matches = self._find_library_matches(bib_nos)
                if library_matches:
                    catalog_dup = True
                    dup_bibs = ",".join(ibrary_matches)
            else:
                catalog_dup = None
                dup_bibs = None
        except BookopsPlatformError:
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
