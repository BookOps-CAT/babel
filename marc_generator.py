# MARC records writer
# this module should be redone with a different approach
# retrieve all records from localstore & create a collection of bibs
# then write each bib - should be easier to handle any errors and will
# not result in files with partial content in case of a problem

from pymarc import MARCWriter, Record, Field
from datetime import date, datetime
import os.path
import shelve
# import logging


import babelstore as db
from convert_price import cents2dollars


# BPL_ORDERS & NYPL_ORDERS values should be customizable for each library
# since the setup may vary between Sierras. Consider creating an interface
# form to record that data and store it in a database table.
BPL_ORDERS = {'acqType': 'p',
              'currency': '1',
              'orderType': 'f',
              'status': '1',  # for funds to be encumbered post-load status must be 'o' on order
              'tloc': 'p'}

NYPL_ORDERS = {'acqType': 'p',
               'orderCode2': 'c',
               'orderCode3': 'f',
               'currency': '1',
               'orderType': 'f',
               'volumes': '1',
               'status': '1',  # for funds to be encumbered post-load status must be 'o' on order
               'tloc': 'p'}  # chekc proper code

# investigate further for complete applicable list of codes
CHAR_CODES = {'rus': '(N',
              'heb': '(2',
              'jpn': '$1',
              'chi': '$1',
              'kor': '$1',
              'ara': '(3',
              'ben': 'Beng'}


class MARCGenerator():

    def __init__(self, order_id):
        # retrieve order record
        self.record_count = 0
        self.order = db.retrieve_record(
            db.Order,
            id=order_id)
        self.order_name = self.order.name
        self.blanketPO = self.order.blanketPO
        # find library MARC code
        if self.order.library_id == 1:
            self.library_code = 'BKL'
        elif self.order.library_id == 2:
            self.library_code = 'NYP'

        # find language code
        record = db.retrieve_record(
            db.Lang,
            id=self.order.lang_id)
        self.lang_code = record.code

        # find vendor code
        record = db.retrieve_record(
            db.Vendor,
            id=self.order.vendor_id)
        self.vendor_name = record.name
        if self.order.library_id == 1:
            self.vendor_code = record.bplCode
        elif self.order.library_id == 2:
            self.vendor_code = record.nyplCode

        # create marc file for records
        user_data = shelve.open('user_data')
        if 'marc_dir' in user_data:
            marc_dir = user_data['marc_dir']
        else:
            marc_dir = ''
        user_data.close()
        file_date = datetime.strftime(date.today(), '%y%m%d')
        fname = self.library_code + '-' + self.vendor_name + '-' + file_date
        n = 0
        fname = marc_dir + fname
        fh = fname + '.mrc'
        while os.path.isfile(fh):
            n += 1
            fh = fname + '(' + str(n) + ')' + '.mrc'
        else:
            self.filehandle = fh

        # find selector code
        records = db.retrieve_all(
            db.Selector,
            'selector_codes',
            id=self.order.selector_id)
        for record in records:
            for sel_code in record.selector_codes:
                if sel_code.library_id == self.order.library_id:
                    self.selector_code = sel_code.code

        # find matType code
        records = db.retrieve_all(
            db.MatType,
            'lib_joins',
            id=self.order.matType_id)
        for record in records:
            for lib_join in record.lib_joins:
                if self.order.library_id == lib_join.library_id:
                    self.matType_bib_code = lib_join.codeB
                    self.matType_ord_code = lib_join.codeO

        records = db.retrieve_all(
            db.OrderSingle,
            'orderSingleLocations',
            order_id=order_id)
        for orderSingle in records:
            # find audn code
            audn = db.retrieve_record(
                db.Audn,
                id=orderSingle.audn_id)
            audn_code = audn.code

            # retrieve bibliographical information
            bib = db.retrieve_record(
                db.BibRec,
                id=orderSingle.bibRec_id)

            distr_records = db.col_preview(
                db.OrderSingleLoc,
                'id', 'location_id', 'fund_id', 'qty',
                orderSingle_id=orderSingle.id)
            distr_locations = []
            distr_funds = []
            qty = 0
            for distr_record in distr_records:
                qty = qty + distr_record.qty
                location_record = db.retrieve_record(
                    db.Location,
                    id=distr_record.location_id)
                branch = db.retrieve_record(
                    db.Branch,
                    id=location_record.branch_id)
                if location_record.audnPresent == 'y':
                    loc_str = branch.code + audn_code + location_record.shelf
                else:
                    loc_str = branch.code + location_record.shelf
                distr_locations.append(loc_str + '/' + str(distr_record.qty))

                fund_record = db.retrieve_record(
                    db.Fund,
                    id=distr_record.fund_id)
                distr_funds.append(
                    fund_record.code + '/' + str(distr_record.qty))
                distr_locations_str = ','.join(distr_locations)
                distr_funds_str = ','.join(distr_funds)

            data = {'library': self.library_code,
                    'lang': self.lang_code,
                    'vendor': self.vendor_code,
                    'selector': self.selector_code,
                    'matType_bib': self.matType_bib_code,
                    'matType_ord': self.matType_ord_code,
                    'blanketPO': self.blanketPO,
                    'audn': audn_code,
                    'po_per_line': orderSingle.po_per_line,
                    'wlo': orderSingle.wlo_id,
                    'priceDisc': str(cents2dollars(orderSingle.priceDisc)),
                    'priceReg': str(cents2dollars(orderSingle.priceReg)),
                    'title': bib.title,
                    'title_trans': bib.title_trans,
                    'author': bib.author,
                    'author_trans': bib.author_trans,
                    'isbn': bib.isbn,
                    'venNo': bib.venNo,
                    'publisher': bib.publisher,
                    'publisher_trans': bib.publisher_trans,
                    'pubDate': bib.pubDate,
                    'pubPlace': bib.pubPlace,
                    'pubPlace_trans': bib.pubPlace_trans,
                    'locQty': distr_locations_str,  # order of locQty must reflect order of funds
                    'funds': distr_funds_str, # order of locQty must reflect order of funds
                    'copies': str(qty)}
            self.make_bib(data)

    def save2marc(self, record):
        """appends records to MARC file"""
        writer = MARCWriter(open(self.filehandle, 'a'))
        writer.write(record)
        self.record_count += 1

    def make_bib(self, order_data):
        """
        creates bib & order record in MARC21 format 
        with UTF-8 encoded charset"""

        record = Record()
        tags = []

        # MARC leader
        if order_data['matType_bib'] in ('h', 'v'):
            MARCmatType = 'g'
        elif order_data['matType_bib'] in ('i', 'u'):
            MARCmatType = 'i'
        elif order_data['matType_bib'] in ('j', 'y'):
            MARCmatType = 'j'
        elif order_data['matType_bib'] == 'a':
            MARCmatType = 'a'
        else:
            MARCmatType = 'a'

        record.leader = '00000n%sm a2200000u  4500' % MARCmatType
        # 001 field
        tags.append(Field(tag='001', data=order_data['wlo']))
        # 008 field
        # needs to take into account differences between different
        # non-print formats
        dateCreated = datetime.strftime(date.today(), '%y%m%d')
        tag008 = dateCreated + r's        xx            000 u ' + \
            order_data['lang'] + r' d'
        if order_data['pubDate'] is not None:
            tag008 = tag008[:7] + order_data['pubDate'] + tag008[11:]
        tags.append(Field(tag='008', data=tag008))

        # 020 field
        if order_data['isbn'] is not None:
            tags.append(Field(tag='020',
                              indicators=[' ', ' '],
                              subfields=['a', order_data['isbn']]))
        # 024 field
        if order_data['venNo'] is not None:
            tags.append(Field(tag='024',
                              indicators=['8', ' '],
                              subfields=['a', order_data['venNo']]))

        # 040 field
        tags.append(Field(tag='040',
                          indicators=[' ', ' '],
                          subfields=['a', order_data['library'],
                                     'b', 'eng',
                                     'c', order_data['library']]))
        # 066 field
        if order_data['lang'] in CHAR_CODES:
            char_code = CHAR_CODES[order_data['lang']]
            tags.append(Field(tag='066',
                              indicators=[' ', ' '],
                              subfields=['c', char_code]))

        # 100 & linked 880
        linked_count = 0
        author_present = False
        linked = False
        if order_data['author_trans'] is not None:
            linked = True
            linked_count + 1
            tags.append(Field(tag='880',
                              indicators=['1', ' '],
                              subfields=['6', '100-0' +
                                         str(linked_count) +
                                         '/' + char_code,
                                         'a', order_data['author']]))
        if order_data['author'] is not None:
            author_present = True
            if linked:
                subfieldA = ['a', order_data['author_trans']]
                subfields = ['6', '880-0' + str(linked_count)]
                subfields.exted(subfieldA)
            else:
                subfieldA = ['a', order_data['author']]
                subfields = subfieldA

            tags.append(Field(tag='100',
                        indicators=['1', ' '],
                        subfields=subfields))

        # 245 field
        # add format to title for non-print mat
        if MARCmatType == 'g':
            order_data['title'] += ' (DVD)'
        elif MARCmatType == 'i':
            order_data['title'] += ' (Audiobook)'
        elif MARCmatType == 'j':
            order_data['title'] += ' (CD)'

        linked = False
        if author_present:
            t245_ind1 = '1'
        else:
            t245_ind1 = '0'
        if order_data['title_trans'] is not None:
            linked = True
            linked_count += 1
            tags.append(Field(tag='880',
                              indicators=[t245_ind1, '0'],
                              subfields=['6', '245-0' + str(linked_count) + '/' + char_code,
                                         'a', order_data['title']]))
        if linked:
            subfieldA = ['a', order_data['title_trans']]
            subfields = ['6', '880-0' + str(linked_count) +
                         '/' + char_code]
            subfields.extend(subfieldA)
        else:
            subfieldA = ['a', order_data['title']]
            subfields = subfieldA

        tags.append(Field(tag='245',
                          indicators=[t245_ind1, '0'],
                          subfields=subfields))

        # 264 & linked 880 field
        subfields = []
        if order_data['pubPlace'] is not None:
            subfieldA = ['a', order_data['pubPlace']]
            subfields.extend(subfieldA)
        if order_data['publisher'] is not None:
            subfieldB = ['b', order_data['publisher']]
            subfields.extend(subfieldB)
        if order_data['pubDate'] is None:
            subfieldC = ['c', '[date not specified]']
        else:
            subfieldC = ['c', order_data['pubDate']]
        subfields.extend(subfieldC)
        tags.append(Field(tag='264',
                          indicators=[' ', '1'],
                          subfields=subfields))

        # 300 field
        if MARCmatType == 'g':
            container = 'videodisc ; 4 3/4 in.'
        elif MARCmatType == 'i':
            container = 'sound disc ; 4 3/4 in.'
        elif MARCmatType == 'j':
            container = 'sound disc ; 4 3/4 in.'
        else:
            container = 'pages ; cm.'

        tags.append(Field(tag='300',
                          indicators=[' ', ' '],
                          subfields=['a', container]))
        # 940 field
        tags.append(Field(tag='940',
                          indicators=[' ', ' '],
                          subfields=['a', 'brief wlo record']))
        # 960 field
        subfields = []
        if order_data['library'] == 'BKL':
            # subfield_A = ['a', BPL_ORDERS['acqType']]  # set by load table
            subfield_M = ['m', BPL_ORDERS['status']]
            subfield_N = ['n', BPL_ORDERS['tloc']]
            subfield_C = ['c', order_data['selector']]
            subfield_Z = ['z', BPL_ORDERS['currency']]
            subfield_D = ['d', order_data['audn']]
            subfields.extend(subfield_C)
            subfields.extend(subfield_D)
        elif order_data['library'] == 'NYP':
            # subfield_A = ['a', NYPL_ORDERS['acqType']]  # set by load table
            subfield_M = ['m', NYPL_ORDERS['status']]
            subfield_N = ['n', NYPL_ORDERS['tloc']]
            subfield_Z = ['z', NYPL_ORDERS['currency']]
            subfield_Y = ['y', NYPL_ORDERS['volumes']]
            subfield_E = ['e', NYPL_ORDERS['orderCode3']]
            subfields.extend(subfield_Y)
            subfields.extend(subfield_E)
        subfield_O = ['o', order_data['copies']]
        subfield_S = ['s', order_data['priceDisc']]
        subfield_T = ['t', order_data['locQty']]
        subfield_U = ['u', order_data['funds']]
        subfield_V = ['v', order_data['vendor']]
        subfield_W = ['w', order_data['lang']]
        subfield_G = ['g', order_data['matType_ord']]

        subfields.extend(subfield_M)
        subfields.extend(subfield_N)
        subfields.extend(subfield_O)
        subfields.extend(subfield_S)
        subfields.extend(subfield_T)
        subfields.extend(subfield_U)
        subfields.extend(subfield_V)
        subfields.extend(subfield_W)
        subfields.extend(subfield_G)
        subfields.extend(subfield_Z)

        tags.append(Field(tag='960',
                          indicators=[' ', ' '],
                          subfields=subfields))
        # 961 field
        subfields = []
        subfield_I = ['i', order_data['wlo']]
        if order_data['po_per_line'] is not None:
            subfield_H = ['h', order_data['po_per_line']]
            subfields.extend(subfield_H)
        subfield_M = ['m', order_data['blanketPO']]
        subfields.extend(subfield_M)
        subfields.extend(subfield_I)
        tags.append(Field(tag='961',
                          indicators=[' ', ' '],
                          subfields=subfields))

        # construct & send to file
        for tag in tags:
            record.add_ordered_field(tag)
        self.save2marc(record)
