"""
This modules handles calls to particular Sierra middleware to discover
any duplicates in the ILS.
"""
import os
import shelve
from typing import Optional


from bookops_bpl_solr import SolrSession
from bookops_nypl_platform import PlatformToken, PlatformSession


try:
    from paths import get_user_data_handle
    from credentials import get_from_vault
except ImportError:
    # tests
    from babel.paths import get_user_data_handle
    from babel.credentials import get_from_vault


def catalog_match(system_id, keyword):
    pass


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

        client_id, client_secret, oauth_server = self._get_credentials()
        # token = self._get_token(client_id, client_secret, oauth_server)
        agent = f"BookOps/Babel"

        # super().__init__(authorization=token, agent=agent)

    def _get_credentials(self):
        user_data_handle = get_user_data_handle()
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
        pass
