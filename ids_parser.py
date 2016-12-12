# parses wlo and related bib and ord numbers from text file


def text_parser(fh):
    file = open(fh, 'r')
    ids = []
    for line in file:
        line = line.replace('\n', '')
        id = line.replace('"', '').split(',')
        ids.append(id)
    return ids
