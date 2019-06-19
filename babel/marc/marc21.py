from datetime import date

from pymarc import MARCWriter, Record, Field


# BPL_ORDERS & NYPL_ORDERS values should be customizable for each library
# since the setup may vary between Sierras. Consider creating an interface
# form to record that data and store it in a database table.
BPL_ORDERS = {
    'acqType': 'p',
    'currency': '1',
    'orderType': 'f',
    'status': '1',  # for funds to be encumbered post-load status must be 'o' on order
    'tloc': 'p'}

NYPL_ORDERS = {
    'acqType': 'p',
    'orderCode2': 'c',
    'orderCode3': 'f',
    'currency': '1',
    'orderType': 'f',
    'volumes': '1',
    'status': '1',  # for funds to be encumbered post-load status must be 'o' on order
    'tloc': 'p'}  # check proper code


def save2marc(outfile, bib):
    try:
        writer = MARCWriter(open(outfile, 'ab'))
        writer.write(bib)
    except WindowsError:
        raise WindowsError
    finally:
        writer.close()


def make_bib(fh, oclc_code, library_code, blanketPO, selector_code, order):
    """creates bib & order record in MARC21 format
       with UTF-8 encoded charset
    """

    record = Record()
    tags = []

    # MARC leader
    if order.mat_bib in ('h', 'v'):
        MARCmatType = 'g'
    elif order.mat_bib in ('i', 'u'):
        MARCmatType = 'i'
    elif order.mat_bib in ('j', 'y'):
        MARCmatType = 'j'
    elif order.mat_bib == 'a':
        MARCmatType = 'a'
    else:
        MARCmatType = 'a'

    record.leader = '00000n%sm a2200000u  4500' % MARCmatType

    # 001 field
    tags.append(Field(tag='001', data=order.wlo))

    # 008 field
    # needs to take into account differences between different
    # non-print formats
    dateCreated = date.strftime(date.today(), '%y%m%d')
    tag008 = f'{dateCreated}s        xx            000 u {order.lang} d'
    if order.resource.pub_date is not None:
        tag008 = tag008[:7] + order.resource.pub_date + tag008[11:]
    tags.append(Field(tag='008', data=tag008))

    # 020 field
    if order.resource.isbn is not None:
        tags.append(Field(tag='020',
                          indicators=[' ', ' '],
                          subfields=['a', order.resource.isbn]))
    # 024 field
    if order.resource.upc is not None:
        tags.append(Field(tag='024',
                          indicators=['1', ' '],
                          subfields=['a', order.resource.upc]))

    # 028 field
    if order.resource.other_no is not None:
        tags.append(Field(tag='028',
                          indicators=['6', '0'],
                          subfields=['a', order.resource.other_no]))

    # 040 field
    tags.append(Field(
        tag='040',
        indicators=[' ', ' '],
        subfields=[
            'a', oclc_code,
            'b', 'eng',
            'c', oclc_code]))

    # # 100
    author_present = False
    if order.resource.author is not None:
        author_present = True
        subfields = ['a', order.resource.author]

        tags.append(Field(
            tag='100',
            indicators=['1', ' '],
            subfields=subfields))

    # 245 field
    # add format to title for non-print mat
    if MARCmatType == 'g':
        order.resource.title += ' (DVD)'
    elif MARCmatType == 'i':
        order.resource.title += ' (Audiobook)'
    elif MARCmatType == 'j':
        order.resource.title += ' (CD)'

    if author_present:
        t245_ind1 = '1'
    else:
        t245_ind1 = '0'
    subfields = ['a', order.resource.title]

    tags.append(Field(
        tag='245',
        indicators=[t245_ind1, '0'],
        subfields=subfields))

    # 264
    subfields = []
    if order.resource.pub_place is not None:
        subfieldA = ['a', order.resource.pub_place]
        subfields.extend(subfieldA)
    if order.resource.publisher is not None:
        subfieldB = ['b', order.resource.publisher]
        subfields.extend(subfieldB)
    if order.resource.pub_date is None:
        subfieldC = ['c', '[date not specified]']
    else:
        subfieldC = ['c', order.resource.pub_date]
    subfields.extend(subfieldC)
    tags.append(Field(
        tag='264',
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

    tags.append(Field(
        tag='300',
        indicators=[' ', ' '],
        subfields=['a', container]))

    # 940 field
    tags.append(Field(
        tag='940',
        indicators=[' ', ' '],
        subfields=['a', 'brief wlo record']))

    # 960 field
    subfields = []
    if oclc_code == 'BKL':
        # subfield_A = ['a', BPL_ORDERS['acqType']]  # set by load table
        subfield_M = ['m', BPL_ORDERS['status']]
        subfield_N = ['n', BPL_ORDERS['tloc']]
        subfield_C = ['c', selector_code]
        subfield_Z = ['z', BPL_ORDERS['currency']]
        subfield_D = ['d', order.audn]
        subfields.extend(subfield_C)
        subfields.extend(subfield_D)
    elif oclc_code == 'NYP':
        # subfield_A = ['a', NYPL_ORDERS['acqType']]  # set by load table
        subfield_M = ['m', NYPL_ORDERS['status']]
        subfield_N = ['n', NYPL_ORDERS['tloc']]
        subfield_Z = ['z', NYPL_ORDERS['currency']]
        subfield_Y = ['y', NYPL_ORDERS['volumes']]
        subfield_E = ['e', NYPL_ORDERS['orderCode3']]
        subfields.extend(subfield_Y)
        subfields.extend(subfield_E)
    subfield_O = ['o', order.copies]
    subfield_Q = ['q', order.order_date]
    subfield_S = ['s', f'{order.resource.price_disc:.2f}']
    subfield_T = ['t', order.locs]
    subfield_U = ['u', order.funds]
    subfield_V = ['v', order.vendor]
    subfield_W = ['w', order.lang]
    subfield_G = ['g', order.mat_ord]

    subfields.extend(subfield_M)
    subfields.extend(subfield_N)
    subfields.extend(subfield_O)
    subfields.extend(subfield_Q)
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
    subfield_I = ['i', order.wlo
    if order.poPerLine is not None:
        subfield_H = ['h', order.poPerLine]
        subfields.extend(subfield_H)
    if blanketPO is not None:
        subfield_M = ['m', blanketPO]
        subfields.extend(subfield_M)
    subfields.extend(subfield_I)
    tags.append(Field(
        tag='961',
        indicators=[' ', ' '],
        subfields=subfields))

    # construct & send to file
    for tag in tags:
        record.add_ordered_field(tag)
    save2marc(fh, record)

