"""
This modules handles calls to NYPL Sierra middleware called Platform.

Retireved and passed along data to other modules should be already sanitized
on this stage.
"""
import os
import logging
from requests import Response
import shelve
from typing import Optional


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

        if self.library not in ("branches", "research", None, ""):
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

        if not self.library:
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

    def get_bib_and_item_data(
        self, sierra_number: str
    ) -> tuple[Optional[dict], Optional[dict]]:
        """
        Retrieves from the Platform bib bibliographic and item data.

        Args:
            sierra_number:          sierra 8 digit bib number

        Returns:
            tuple of two dictionaries (bib_data, item_data)
        """
        bib = self._get_bib(sierra_number)
        if bib:
            bib_data = self._parse_bibliographic_data(bib)
        else:
            bib_data = None

        items = self._get_items(sierra_number)
        if items:
            item_data = self._parse_item_data(items)
        else:
            item_data = None

        return bib_data, item_data

    def _parse_bibliographic_data(self, data: dict) -> dict:
        """
        Parses Platform response of the /bibs/{nyplSource}/{id} endpoint

        Args:
            data:                   Platform response as dictionary

        Returns:
            bib#, author, title, pub data as dictionary
        """
        data = data["data"]
        return dict(
            bibNo=data["id"],
            title=data["title"],
            author=data["author"],
            pubDate=data["publishYear"],
            pubPlace=data["country"]["name"],
        )

    def _parse_item_data(self, data: dict) -> list[dict]:
        """
        Parses Platform response of the bibs/{nyplSource}/{id}/items endpoint.

        Args:
            data:                   Platform response as dictionary

        Returns:
            list of dict with loc_code, loc_name, status, circ, last_check
        """
        items = []
        for item in data["data"]:
            try:
                lastCheck = f"{item['fixedFields']['78']['value'][:10]}"
            except KeyError:
                lastCheck = "-"
            items.append(
                dict(
                    locCode=item["location"]["code"],
                    locName=item["location"]["name"],
                    status=item["status"]["display"],
                    circ=f"{item['fixedFields']['76']['value']}+{item['fixedFields']['77']['value']}",
                    lastCheck=lastCheck,
                )
            )
        return items

    def _get_bib(self, sierra_number: str) -> Optional[dict]:
        """
        Makes a request for given Sierra record.

        Args:
            sierra_number:          sierra 8 digit bib number

        Returns:
            json response as dict
        """
        try:
            response = self.get_bib(id=sierra_number)
        except BookopsPlatformError:
            mlogger.warning(
                f"Unable to retireve bib {sierra_number} data from Platform."
            )
            response = None

        if response and response.status_code == 200:
            return response.json()
        else:
            return None

    def _get_items(self, sierra_number: str) -> Optional[dict]:
        """
        Makes a request for items attached to given sierra bib nubmer.

        Args:
            sierra_number:          sierra 8 digit bib number

        Returns:
            json response as dict
        """
        try:
            response = self.get_bib_items(id=sierra_number)
        except BookopsPlatformError:
            mlogger.warning(
                f"Unable to retrieve bib {sierra_number} item data from Platform."
            )
            response = None

        if response and response.status_code == 200:
            return response.json()
        else:
            return None

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
