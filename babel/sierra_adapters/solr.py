"""
This module handles requests to BPL Solr.
"""
import os
import logging
import shelve
from typing import Optional

from bookops_bpl_solr import SolrSession
from bookops_bpl_solr.session import BookopsSolrError

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
