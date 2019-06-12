# xlsx spreadsheet parser
# how about list of namedtuples as output parsing spreadsheet? pros: immutable, access by name, default values

import logging

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string
# from openpyxl import Workbook


from data.data_objs import VenData
from data import validators


mlogger = logging.getLogger('babel_logger')


class SheetReader:

    def __init__(self, file):
        self.wb = load_workbook(
            filename=file,
            data_only=True)
        self.ws = self.wb.active
        self.max_row = 0
        self.max_column = 1
        for row in self.ws.rows:
            self.max_row += 1
            max_column = len(row)
            if max_column > self.max_column:
                self.max_column = max_column
        self.range = 'A1:' + str(
            get_column_letter(self.max_column)) + str(self.max_row)

    def __iter__(self):
        for row in self.ws[self.range]:
            data = []
            for cell in row:
                data.append(cell.value)
            yield data


class ResourceDataReader:
    """
    Parses specified rows and columns of the xlsx spreadsheet
    The reader can be iterater over in a loop

    Arguments:
    ----------
    fh: str
        path to xlsx spreadsheet
    header_row: int
        row number of a header, index starts with 0
    title_col: int
        title column number, index starts with 0
    add_title_col: int
        additional title column, index starts with 0
    author_col: int
        author column number, index starts with 0
    series_col: int
        series column number, index starts with 0
    publisher_col: int
        publisher column number, index starts with 0
    pub_datae_col: int
        publicattion column number, index starts with 0
    summary_col: int
        summary column number, index starts with 0
    isbn_col: int
        ISBN column number, index starts with 0
    upc_col: int
        UPC column number, index starts with 0
    other_no_col: int
        publisher interal ID, etc. column number, index starts with 0
    price_list_col: int
        list price column number, index starts with 0
    price_disc: int
        discounted price column number, index starts with 0
    desc_url: int
        URL of description column number, index starts with 0

    """

    def __init__(
            self, fh,
            header_row=None,
            title_col=None,
            add_title_col=None,
            author_col=None,
            series_col=None,
            publisher_col=None,
            pub_date_col=None,
            pub_place_col=None,
            summary_col=None,
            isbn_col=None,
            upc_col=None,
            other_no_col=None,
            price_list_col=None,
            price_disc_col=None,
            desc_url_col=None,
            misc_col=None):

        self.header_row = header_row
        self.title_col = title_col
        self.add_title_col = add_title_col
        self.author_col = author_col
        self.series_col = series_col
        self.publisher_col = publisher_col
        self.pub_date_col = pub_date_col
        self.pub_place_col = pub_place_col
        self.summary_col = summary_col
        self.isbn_col = isbn_col
        self.upc_col = upc_col
        self.other_no_col = other_no_col
        self.price_list_col = price_list_col
        self.price_disc_col = price_disc_col
        self.desc_url_col = desc_url_col
        self.misc_col = misc_col

        try:
            self.min_row = header_row + 1
        except TypeError:
            raise AttributeError(
                'Header row number is a required argument')

        if not title_col:
            raise AttributeError(
                'Title column letter is a required argument')

        wb = load_workbook(
            filename=fh,
            read_only=True,
            keep_vba=False,
            data_only=True,
            keep_links=True)
        self.ws = wb.active

    def __iter__(self):
        for row in self.ws.iter_rows(
                values_only=True, min_row=self.min_row):
            data = self._map_content(row)
            if data:
                data = self._normalize(data)
                yield data

    def _normalize(self, data):
        data = data._replace(
            title=validators.normalize_whitespaces(data.title),
            add_title=validators.normalize_whitespaces(data.add_title),
            author=validators.normalize_whitespaces(data.author),
            series=validators.normalize_whitespaces(data.series),
            publisher=validators.normalize_whitespaces(data.publisher),
            pub_date=validators.normalize_date(data.pub_date),
            pub_place=validators.normalize_whitespaces(data.pub_place),
            summary=validators.normalize_whitespaces(data.summary),
            isbn=validators.normalize_isbn(data.isbn),
            upc=validators.value2string(data.upc),
            other_no=validators.value2string(data.other_no),
            price_list=validators.normalize_price(data.price_list),
            price_disc=validators.normalize_price(data.price_disc),
            misc=validators.normalize_whitespaces(data.misc))
        return data

    def _map_content(self, row):
        """
        returns rows where title column has some value
        """
        kwargs = dict()
        if row[self.title_col] is not None:
            title = row[self.title_col].strip()
            if title != '':
                kwargs['title'] = title
                if self.add_title_col is not None:
                    kwargs['add_title'] = row[self.add_title_col]
                if self.author_col is not None:
                    kwargs['author'] = row[self.author_col]
                if self.series_col is not None:
                    kwargs['series'] = row[self.series_col]
                if self.publisher_col is not None:
                    kwargs['publisher'] = row[self.publisher_col]
                if self.pub_date_col is not None:
                    kwargs['pub_date'] = row[self.pub_date_col]
                if self.pub_place_col is not None:
                    kwargs['pub_place'] = row[self.pub_place_col]
                if self.summary_col is not None:
                    kwargs['summary'] = row[self.summary_col]
                if self.isbn_col is not None:
                    kwargs['isbn'] = row[self.isbn_col]
                if self.upc_col is not None:
                    kwargs['upc'] = row[self.upc_col]
                if self.other_no_col is not None:
                    kwargs['other_no'] = row[self.other_no_col]
                if self.price_list_col is not None:
                    kwargs['price_list'] = row[self.price_list_col]
                if self.price_disc_col is not None:
                    kwargs['price_disc'] = row[self.price_disc_col]
                if self.desc_url_col is not None:
                    kwargs['desc_url'] = row[self.desc_url_col]
                if self.misc_col is not None:
                    kwargs['misc'] = row[self.misc_col]

                return VenData(**kwargs)
