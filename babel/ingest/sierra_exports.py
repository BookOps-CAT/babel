import csv


from errors import BabelError


BPL_IDS_HEADER = ['VEN TITL #', 'RECORD #', 'RECORD #']
NYPL_IDS_HEADER = ['VEN TITL #', 'RECORD #(ORDER)', 'RECORD #(BIBLIO)']


def get_sierra_ids(source_fh, system_id):
    """
    Sierra IDs export parser
    args:
        source_fh: str, filehandle of Sierra export file
        system_id: str, 'BPL' or 'NYPL'
    returns:
        ids: list of id lists, [wlo, oid, bid]
    """

    ids = []
    with open(source_fh, 'r') as file:
        reader = csv.reader(file, delimiter=',', quotechar='"')
        header = reader.__next__()

        # verify Sierra export has a correct format
        if system_id == 1:
            if not header == BPL_IDS_HEADER:
                raise BabelError(
                    'Exported from Sierra IDs should be in\n'
                    'the following order:\n\t'
                    '{}'.format('\n\t'.join(BPL_IDS_HEADER)))
        elif system_id == 2:
            if not header == NYPL_IDS_HEADER:
                raise BabelError(
                    'Exported from Sierra IDs should be in\n'
                    'the following order:\n\t'
                    '{}'.format('\n\t'.join(NYPL_IDS_HEADER)))

        for row in reader:
            if len(row) == 3:
                ids.append(row)

    return ids
