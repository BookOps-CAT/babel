# validators of entered data
# very preliminary stage, more work needed to beef it up
import celldata_parser as input_parser


def vendor_form(data):
    msg = ''
    msg1 = "-required elements: " \
        "'name', 'save as', 'BPL Sierra code', and 'NYPL Sierra code'"
    for key in data:
        if key is not 'note' and data[key] == '':
            msg = msg1
            break

    if len(data['note']) > 250:
        msg = msg + "\n-" \
            "notes cannot be longer than 250 characters"
    if len(data['name']) > 25:
        msg = msg + "\n-" \
            "'save as' cannot be longer than 25 characters"
    if len(data['nameFormal']) > 50:
        msg = msg + "\n-" \
            "'name' cannot be longer than 50 characters"
    if len(data['bplCode']) > 5:
        msg = msg + "\n-" \
            "'BPL Sierra code' cannot be longer than 5 characters"
    if len(data['nyplCode']) > 5:
        msg = msg + "\n-" \
            "'NYPL Sierra code' cannot be longer than 5 characters"

    if msg == '':
        return None
    else:
        return msg


def collaborator_form(data):
    msg = ''
    msg1 = "-required elements: " \
        "'library', 'save as', and 'collaborator 1'"
    for key in data:
        if key not in ('collab2', 'collab3', 'collab4', 'collab5') \
                and data[key] == '':
            msg = msg1
            break

    if msg == '':
        return None
    else:
        return msg


def location_form(data):
    msg = ''
    msg1 = "all fields are required"
    for key in data:
        if key in ('library_id', 'matType_id', 'branch_id'):
            if data[key] == 0:
                msg = msg1
                break
        elif data[key] == '':
            msg = msg1
            break
    if len(data['name']) > 10:
        msg = msg + "\n-"\
            "location shorthand cannot be longer than 10 characters"
    if len(data['shelf']) > 3:
        msg = msg + "\n-" \
            "shelf code cannot be longer than 3 characters"
    if (len(data['shelf']) == 3) and (data['audnPresent'] == 'y'):
        msg = msg + "\n-" \
            "shelf location must be no longer than 2 characters if" \
            "audience code is present"
    if msg == '':
        return None
    else:
        return msg


def distribution_form(data):
    rows = 0
    msg = ''
    for key in data:
        if (data[key][0] != '') and (data[key][1] != ''):
            rows += 1

    if rows == 0:
        msg1 = 'distribution must have at least one code\n' \
               'and associated locations with quantities'
        msg = msg + msg1

    if msg == '':
        return None
    else:
        return msg


def fund_form(data):
    msg = ''
    if data['code'] == '':
        msg1 = 'Fund code field is required\n'
        msg = msg + msg1
    if len(data['code']) > 10:
        mgs2 = 'Fund code cannot be longer than 10 characters\n'
        msg = msg + mgs2
    if len(data['branches']) == 0:
        msg3 = 'At least one branch has to be selected\n'
        msg = msg + msg3
    if len(data['matTypes']) == 0:
        msg4 = 'At least one material type has to be selected\n'
        msg = msg + msg4
    if len(data['audns']) == 0:
        msg5 = 'At least one audience type has to be selected\n'
        msg = msg + msg5

    if msg == '':
        return None
    else:
        return msg


def vendorSheet_form(data):
    # validates input data of a vendor sheet structure
    e = []
    mandatory = (
        'name',
        'lang',
        'matType',
        'vendor',
        'head_row',
        'title_col',
    )
    columns = (
        'title_col',
        'priceDisc_col',
        'author_col',
        'isbn_col',
        'publisher_col',
        'pubDate_col',
        'pubPlace_col',
        'priceReg_col',
        'venNum_col'
    )

    if len(data['name']) > 25:
        m = 'sheet template name cannot be longer than 25 chararctes'
        e.append(m)
    if len(data['desc']) > 250:
        m = 'description field cannot be longer than 250 characters'
        e.append(m)
    if data['head_row']:
        try:
            int(data['head_row'])
        except:
            m = 'heading row must be an integer'
            e.append(m)
    for field in mandatory:
        if data[field] == '':
            m = 'missing requried fields: %s' % field
            e.append(m)
    unique_val = set()
    for col in columns:
        v = data[col]
        if v in unique_val and v != '':
            m = "column '%s' entered more than once" % v
            e.append(m)
        else:
            unique_val.add(v)
        for c in data[col]:
            if c not in ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                m = 'column desingation must consist of letters'
                e.append(m)
                break
        if len(data[col]) > 2:
            m = 'column designation cannot consist of more then 2 letters'
            e.append(m)
            break

    if len(e) == 0:
        return None
    else:
        return e


def eval_distr_unit(data):
    # validates distribution data

    loc = data['location']
    fund = data['fund']
    qty = data['qty']

    if data['distr_id'] is None:
        new = True
    else:
        new = False

    if loc == -1 and fund == -1 and qty == '':
        if data['distr_id'] is None:
            complete = None
    elif loc == -1 or fund == -1 or qty == '':
        complete = False
    else:
        complete = True

    try:
        int(qty)
        valid_qty_type = True
    except ValueError:
        valid_qty_type = False

    return (new, complete, valid_qty_type)


def bib_validation(bib):
    error = None
    for key in bib:
        if key == 'bib_id':
            pass
        else:
            bib[key] = bib[key].strip()
            if bib[key] == '':
                bib[key] = None

    # required element
    if bib['title'] is None:
        error = 'empty title field'

    # parse isbn & date input
    isbn = input_parser.parse_isbn(bib['isbn'])
    date = input_parser.parse_year(bib['date'])
    bib['isbn'] = isbn
    bib['date'] = date
    # print bib
    return (error, bib)
