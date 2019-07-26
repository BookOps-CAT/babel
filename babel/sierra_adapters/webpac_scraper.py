# adapter for web scraping classic III WebPac
import logging
import re


from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException, Timeout


from errors import BabelError


BPL_URL = 'https://iii.brooklynpubliclibrary.org'
NYPL_URL = 'https://catalog.nypl.org'

TIME_OUT = 10  # seconds


mlogger = logging.getLogger('babel_logger')


def get_html(system_id, keyword):
    """
    retrieves html code from given url
    args:
        url: str
    returns:
        html: bytes
    """

    if system_id == 1:
        url = f'{BPL_URL}/search/i{keyword}'
    elif system_id == 2:
        url = f'{NYPL_URL}/search/i{keyword}'

    if keyword:
        headers = {'user-agent': 'BookOps/Babel'}

        try:
            response = requests.get(url, headers=headers, timeout=TIME_OUT)
            mlogger.debug(
                f'WebScraper request: {response.url}, '
                f'response code: {response.status_code}')

            if response.status_code == requests.codes.ok:
                return response.content

        except Timeout:
            mlogger.error('Webscraper timed out.')
            raise BabelError(
                'Request for a page timed out. Terminating.')
        except RequestException:
            pass


def catalog_match(system_id, keyword):
    """
    Scrapes html page of OPAC of the keyword search
    args:
        system_id: int, datastore system did
        keyword: str, ISBN or UPC
    returns: bool, False if no matches found or True if dup present
    """

    html = get_html(system_id, keyword)
    if html is not None:
        soup = BeautifulSoup(html, 'html.parser')
        res = soup.body.find('td', text=re.compile('^No matches found.*'))
        if res:
            return False
        else:
            return True
    else:
        return False
