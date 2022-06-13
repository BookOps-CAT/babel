"""
This modules handles calls to particular Sierra middleware to discover
any duplicates in the ILS.
"""
import os
import shelve
from typing import Optional, Union


from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformToken, PlatformSession


try:
    from paths import get_user_data_handle
    from credentials import get_from_vault
except ImportError:
    # tests
    from babel import paths
    from babel.credentials import get_from_vault


def catalog_match(middleware: Union[PlatformSession, SolrSession], keywords: list[str]):
    catalog_dup = None
    dup_bibs = []

    catalog_dup, dup_bibs = middleware.search(keywords)

    return catalog_dup, dup_bibs


class NypPlatform(PlatformSession):
    def __init__(self, library: str) -> None:
        """
        Authenticates and opens a session with NYPL Platform.
        Relies on credentials stores in Windows Credential Manager.

        Args:
                library:            'branch' or 'research'
        """
        self.library = library  # branch or research
        if self.library not in ("branch", "research", None):
            raise ValueError("Invalid library argument passed.")
        self.agent = "BookOps/Babel"

        client_id, client_secret, oauth_server = self._get_credentials()
        token = self._get_token(client_id, client_secret, oauth_server)

        super().__init__(authorization=token, agent=self.agent)

    def _get_credentials(self) -> tuple[str, str, str]:
        """Retrieves NYPL Platform credentials from user_data and vault"""
        user_data_handle = paths.get_user_data_handle()
        user_data = shelve.open(user_data_handle)

        config = user_data["nyp_platform"]
        oauth_server = config["PLATFORM_OAUTH_SERVER"]
        client_id = config["PLATFORM_CLIENT_ID"]
        client_secret = get_from_vault("babel_platform", client_id)

        user_data.close()

        return client_id, client_secret, oauth_server

    def _get_token(
        self, client_id: str, client_secret: str, oauth_server: str
    ) -> Optional[PlatformToken]:
        """Obtains NYPL Platform access token"""
        token = PlatformToken(client_id, client_secret, oauth_server, self.agent)
        return token

    def _parse_response(self, response) -> tuple[Optional[str], Optiona[str]]:
        pass

    def search(self, keywords: list[str]) -> response[Response]:
        response = self.get_bib_list(standard_number=keywords)
        catalog_dup, dup_bibs = self._parse_response(response)


class BplSolr(SolrSession):
    def __init__(self):
        pass
