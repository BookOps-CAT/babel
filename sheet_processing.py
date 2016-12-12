# xlsx reader & writer

from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.styles import Protection, Font, PatternFill
import os.path

from convert_price import dollars2cents, cents2dollars


class SheetManipulator:

    def __init__(self, file):
        # define styles for writing sheet
        self.font = Font(bold=True)
        self.red_font = Font(bold=True, color='CC0000')
        self.white_font = Font(color='FFFFFF')
        self.protected = Protection(locked=True,
                                    hidden=False)

        self.wb = load_workbook(filename=file,
                                data_only=True,
                                guess_types=False)
        self.ws = self.wb.active
        self.max_r = 0
        self.max_c = 1
        for row in self.ws.rows:
            self.max_r += 1
            max_c = len(row)
            if max_c > self.max_c:
                self.max_c = max_c
        self.range = 'A1:' + str(
            get_column_letter(self.max_c)) + str(self.max_r)
        self.last_col = get_column_letter(self.max_c)

    def get_column_letters(self):
        column_letters = []
        for column in range(1, self.max_c + 1):
            column_letters.append(get_column_letter(column))
        return column_letters

    def extract_data(self):
        self.sheet_data = []
        # find last column & last row (column not accurate in openpyxl)
        # for row in tuple(self.ws.iter_rows(self.range)):
        for row in self.ws[self.range]:
            row_data = []
            for cell in row:
                row_data.append(cell.value)
            self.sheet_data.append(row_data)
        return self.sheet_data

    def cart_sheet(self, fname, **kwargs):
        self.head_row = self.ws[
            'A' + str(kwargs['head_row']) +
            ':' + self.last_col + str(kwargs['head_row'])]
        self.data_range = 'A' + str(
            kwargs['head_row'] + 1) + ':' + str(
            get_column_letter(self.max_c)) + str(
            self.max_r + 1)
        self.new_wb = Workbook()
        self.new_ws_cart = self.new_wb.active
        self.new_ws_cart.title = 'cart'

        # reference legend area
        dr = 1
        distrLegend = kwargs['distrDetails'].split('\n')
        for line in distrLegend[2:]:
            self.new_ws_cart.cell(row=dr, column=1).value = line
            self.new_ws_cart.cell(row=dr, column=1).font = self.font
            self.new_ws_cart.cell(row=dr, column=1).protection = self.protected
            dr += 1
        ar = 1
        audnLegend = [
            'audience:',
            'empty cell = adult',
            'j = juvenile', 'y = young adult']
        for line in audnLegend:
            self.new_ws_cart.cell(row=ar, column=5).value = line
            self.new_ws_cart.cell(row=ar, column=5).font = self.font
            self.new_ws_cart.cell(row=ar, column=5).protection = self.protected
            ar += 1
        c = 8
        for key, value in kwargs['codeTotalQntBranch'].items():
            # change font to white and protect to hide
            self.new_ws_cart.cell(row=1, column=c).value = key
            self.new_ws_cart.cell(row=1, column=c).font = self.font
            self.new_ws_cart.cell(row=2, column=c).value = value[0]
            self.new_ws_cart.cell(row=2, column=c).font = self.font
            self.new_ws_cart.cell(row=3, column=c).value = value[1]
            self.new_ws_cart.cell(row=3, column=c).font = self.font
            c += 1
        # codes_range must be in A1 notation
        codes_range = 'H1:%s3' % (get_column_letter(c - 1))
        # headings row
        extra_columns = ()
        standard_columns = (
            'Distribution',
            'Branches',  # optional ask if needed,  # optional ask if needed
            'Total Qty',
            'Total Price',  # optional ask if needed
            'Audience')
        extra_columns = extra_columns + kwargs['collabs']
        if kwargs['priceDefault'] != 0.0 or kwargs['priceDisc_col'] == '':
            extra_columns = extra_columns + ('Unit Price', )
            shifted_price_col = get_column_letter(len(extra_columns))
        else:
            price_col = kwargs['priceDisc_col']
            shifted_price_col_num = column_index_from_string(price_col) + len(extra_columns) + len(standard_columns)
            shifted_price_col = get_column_letter(shifted_price_col_num)
        distr_col = len(extra_columns) + 1
        total_qty_col = len(extra_columns) + 3
        total_price_col = len(extra_columns) + 4
        extra_columns = extra_columns + standard_columns
        shift_index = len(extra_columns)
        # add sheet totals
        if ar > dr:
            lr = ar
        else:
            lr = dr
        head_row = lr + 5
        self.new_ws_cart.cell(row=lr + 1, column=1).value = '# of titles='
        self.new_ws_cart.cell(row=lr + 1, column=1).font = self.font
        self.new_ws_cart.cell(row=lr + 2, column=1).value = '# of copies='
        self.new_ws_cart.cell(row=lr + 2, column=1).font = self.font
        self.new_ws_cart.cell(row=lr + 3, column=1).value = 'total price='
        self.new_ws_cart.cell(row=lr + 3, column=1).font = self.font
        self.new_ws_cart.cell(row=lr + 1, column=2).value = "=COUNTA(%s%s:%s1000)" % (
            get_column_letter(distr_col), head_row + 1, get_column_letter(distr_col))
        self.new_ws_cart.cell(row=lr + 1, column=2).font = self.red_font
        self.new_ws_cart.cell(row=lr + 2, column=2).value = '=SUMIF(%s%s:%s1000, ">0")' % (
            get_column_letter(total_qty_col), head_row + 1, get_column_letter(total_qty_col))
        self.new_ws_cart.cell(row=lr + 2, column=2).font = self.red_font
        self.new_ws_cart.cell(row=lr + 3, column=2).value = '=SUMIF(%s%s:%s1000, ">0")' % (
            get_column_letter(total_price_col), head_row + 1, get_column_letter(total_price_col))
        self.new_ws_cart.cell(row=lr + 3, column=2).font = self.red_font
        self.new_ws_cart.cell(row=lr + 4, column=1).value = None

        new_headings = []
        for col in extra_columns:
            new_headings.append(col)
        for heading in self.head_row:
            for data in heading:
                new_headings.append(data.value)
        self.new_ws_cart.append(new_headings)
        # remaining rows
        # for row in tuple(self.ws.iter_rows(self.data_range)):
        row_counter = 0
        for row in self.ws[self.data_range]:
            row_counter += 1
            # add trimming for formulae
            totQnt_formula = '=HlOOKUP(LEFT(TRIM(INDIRECT("R"&ROW()&"C%s", FALSE)),1),%s,2,FALSE)+IF(LEN(INDIRECT("R"&ROW()&"C%s",FALSE))=2,HLOOKUP(RIGHT(TRIM(INDIRECT("R"&ROW()&"C%s",FALSE)),1),%s,2,FALSE),0)' % (
                distr_col, codes_range, distr_col, distr_col, codes_range)
            totPrice_formula = '=HLOOKUP(LEFT(TRIM(INDIRECT("R"&ROW()&"C%s", FALSE)),1),%s,2,FALSE)*INDIRECT("%s"&ROW())+IF(LEN(INDIRECT("R"&ROW()&"C%s",FALSE))=2,HLOOKUP(RIGHT(TRIM(INDIRECT("R"&ROW()&"C%s",FALSE)),1),%s,2,FALSE)*INDIRECT("%s"&ROW()),0)' % (
                distr_col, codes_range, shifted_price_col,
                distr_col, distr_col, codes_range, shifted_price_col)
            branch_formula = '=CONCATENATE((HlOOKUP(LEFT(TRIM(INDIRECT("R"&ROW()&"C%s", FALSE)),1),%s,3,FALSE)),(IF(LEN(INDIRECT("R"&ROW()&"C%s",FALSE))=2,HLOOKUP(RIGHT(TRIM(INDIRECT("R"&ROW()&"C%s",FALSE)),1),%s,3,FALSE),"")))' % (
                distr_col, codes_range, distr_col, distr_col, codes_range)
            new_values = []
            col_counter = 0
            for col in extra_columns:
                col_counter += 1
                if col == 'Total Qty':
                    new_values.append(totQnt_formula)
                elif col == 'Total Price':
                    new_values.append(totPrice_formula)
                elif col == 'Branches':
                    new_values.append(branch_formula)
                elif col == 'Unit Price':
                    if kwargs['priceDefault'] != 0.0:
                        priceDefault = dollars2cents(kwargs['priceDefault'])
                        priceDefault = cents2dollars(priceDefault)
                        new_values.append(priceDefault)
                    else:
                        discount = kwargs['discount']
                        discount = str(discount).zfill(2)
                        discount = '0.' + discount
                        discount = float(discount)
                        # kwargs['priceReg_col']
                        list_price = self.ws[
                            kwargs['priceReg_col'] +
                            str(kwargs['head_row'] + row_counter)
                        ].value
                        if list_price is None:
                            list_price = 0.0
                        else:
                            disc_price = list_price - (list_price * discount)
                            disc_price = dollars2cents(disc_price)
                            disc_price = cents2dollars(disc_price)
                        new_values.append(disc_price)
                elif col == 'Audience':
                    audn_col = col_counter
                    new_values.append(None)
                else:
                    new_values.append(None)
            old_values = []
            for cell in row:
                old_values.append(cell.value)
            new_values.extend(old_values)
            self.new_ws_cart.append(new_values)

        # record new column & rows structure
        pre_shift_metadata = kwargs.copy()
        shifted_metadata = {}
        columns = ('title_col', 'author_col',
                   'isbn_col', 'venNum_col',
                   'publisher_col', 'pubDate_col',
                   'pubPlace_col', 'priceReg_col')
        for key, value in pre_shift_metadata.items():
            if key in columns:
                if value != '':
                    shifted_metadata[key] = column_index_from_string(
                        value) + shift_index
                elif value == '':
                    shifted_metadata[key] = value

        shifted_metadata['vendorSheetTemplate_id'] = kwargs['sheetTemp_id']
        shifted_metadata['distrTemplate_id'] = kwargs['distr_id']
        shifted_metadata['head_row'] = head_row
        shifted_metadata['distr_col'] = distr_col
        shifted_metadata['audn_col'] = audn_col
        shifted_metadata['priceDisc_col'] = column_index_from_string(
            shifted_price_col)

        # create new sheet where metadata is recorded
        meta_str = ''
        self.new_ws_meta = self.new_wb.create_sheet('meta')
        for key, value in shifted_metadata.items():
            meta_str = meta_str + key + '=' + str(value) + ';'
        self.new_ws_meta.cell(row=1, column=1).value = meta_str
        # set font white and protect
        # self.new_ws_cart.cell(row=1, column=15).font = self.white_font
        # self.new_ws_cart.cell(row=2, column=15).font = self.white_font

        # determine file name
        n = 0
        fh = fname + '.xlsx'
        while os.path.isfile(fh):
            n += 1
            fh = fname + '(' + str(n) + ')' + '.xlsx'
        else:
            filehandle = fh
        self.new_wb.save(filename=filehandle)
        return filehandle

    def extract_meta(self):
        self.ws_meta = self.wb['meta']
        meta_str = self.ws_meta['A1'].value
        meta_lst = meta_str.split(';')
        self.metadata = {}
        for item in meta_lst:
            pos = item.find('=')
            key = item[:pos]
            value = item[pos + 1:]
            if value != '':
                value = int(value)
                if key in (
                    'title_col', 'distr_col', 'audn_col', 'author_col',
                    'isbn_col', 'venNum_col', 'publisher_col',
                    'pubDate_col', 'pubPlace_col', 'priceReg_col',
                    'priceDisc_col'):
                        value = get_column_letter(value)
            self.metadata[key] = value
        self.start_row = self.metadata['head_row']
        return self.metadata

    def find_orders(self, distr_codes):
        self.orders = []
        self.total_cost = 0.0
        self.distr_codes = distr_codes
        self.ws_orders = self.wb['cart']
        self.order_range = 'A' + str(
            self.start_row + 1) + ':' + str(
            get_column_letter(self.max_c)) + str(
            self.max_r + 1)
        distr_col_num = column_index_from_string(self.metadata['distr_col'])

        selected_rows = []
        r = self.metadata['head_row'] + 1

        for row in self.ws_orders[self.order_range]:
            cell_num = 1
            for cell in row:
                if cell_num == distr_col_num:
                    codes_qty = 0
                    if cell.value is not None:
                        for code in str(cell.value):
                            try:
                                code = code.upper()
                            except:
                                pass
                            if code in self.distr_codes:
                                codes_qty += 1
                        # append only if all codes in cel match self.distr_codes
                        if codes_qty == len(str(cell.value)):
                            selected_rows.append(r)
                            break
                cell_num += 1
            r += 1

        for row_num in selected_rows:
            order = {}
            for key, value in self.metadata.items():
                if key in (
                    'title_col', 'distr_col', 'audn_col', 'author_col',
                    'isbn_col', 'venNum_col', 'publisher_col',
                    'pubDate_col', 'pubPlace_col', 'priceReg_col',
                    'priceDisc_col'
                ):
                    if value != '':
                        cell = self.ws_orders[
                            self.metadata[key] + str(row_num)]
                        content = cell.value
                        order[key] = content
                        if key == 'priceDisc_col':
                            self.total_cost = self.total_cost + content
                        if key == 'distr_col':
                            try:
                                order['distr_col'] = order['distr_col'].upper()
                            except:
                                order['distr_col'] = order['distr_col']
                    else:
                        order[key] = None

            self.orders.append(order)
            self.order_qty = len(selected_rows)
        # summary can serve to check if selected = added to db
        return {'summary': None, 'orders': self.orders}


def create_order(fname, library, data):
    font_bold = Font(bold=True)
    fill_gray = PatternFill(fill_type='solid',
                            start_color='C4C5C6',
                            end_color='C4C5C6')
    order_wb = Workbook()
    order_ws = order_wb.active
    # title_count = 0
    address_line1 = 'BookOps %s' % library
    address_line2 = '31-11 Thomson Avenue'
    address_line3 = 'Long Island City, NY 11101'

    order_ws.cell(row=2, column=1).value = address_line1
    order_ws.cell(row=2, column=1).font = font_bold
    order_ws.cell(row=3, column=1).value = address_line2
    order_ws.cell(row=3, column=1).font = font_bold
    order_ws.cell(row=4, column=1).value = address_line3
    order_ws.cell(row=4, column=1).font = font_bold

    # headers
    order_ws.cell(row=6, column=1).value = '#'
    order_ws.cell(row=6, column=1).fill = fill_gray
    order_ws.cell(row=6, column=2).value = 'SKU'
    order_ws.cell(row=6, column=2).fill = fill_gray
    order_ws.cell(row=6, column=3).value = 'ISBN'
    order_ws.cell(row=6, column=3).fill = fill_gray
    order_ws.cell(row=6, column=4).value = 'Title'
    order_ws.cell(row=6, column=4).fill = fill_gray
    order_ws.cell(row=6, column=5).value = 'Author'
    order_ws.cell(row=6, column=5).fill = fill_gray
    order_ws.cell(row=6, column=6).value = 'Unit Price'
    order_ws.cell(row=6, column=6).fill = fill_gray
    order_ws.cell(row=6, column=7).value = 'Copies'
    order_ws.cell(row=6, column=7).fill = fill_gray
    order_ws.cell(row=6, column=8).value = 'Total Price'
    order_ws.cell(row=6, column=8).fill = fill_gray
    order_ws.cell(row=6, column=9).value = 'o Number'
    order_ws.cell(row=6, column=9).fill = fill_gray

    r = 1
    for title in data:
        row = []
        row.append(r)
        row.extend(title)
        order_ws.append(row)
        r += 1
    last_r = 6 + r
    order_ws.cell(row=last_r + 2, column=3).value = 'total copies='
    order_ws.cell(row=last_r + 2, column=3).fill = fill_gray
    order_ws.cell(row=last_r + 2, column=4).value = '=SUM(G7:G' + str(last_r) + ')'
    order_ws.cell(row=last_r + 2, column=4).fill = fill_gray
    order_ws.cell(row=last_r + 3, column=3).value = 'total cost='
    order_ws.cell(row=last_r + 3, column=3).fill = fill_gray
    order_ws.cell(row=last_r + 3, column=4).value = '=SUM(H7:H' + str(last_r) + ')'
    order_ws.cell(row=last_r + 3, column=4).fill = fill_gray

    # determine if new file name needed
    n = 0
    fh = fname + '.xlsx'
    while os.path.isfile(fh):
            n += 1
            fh = fname + '(' + str(n) + ')' + '.xlsx'
    else:
        filehandle = fh
    try:
        order_wb.save(filename=filehandle)
        return filehandle
    except:
        return None
