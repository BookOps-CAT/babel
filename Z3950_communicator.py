# handles Z3950 requests

from PyZ3950 import zoom
import logging


# create logger
module_logger = logging.getLogger('babel_logger.z3950')

# query qualifiers use CCL specs
# more on CCL @ www.indexdata.com/yaz/doc/tools.html#CCL

qualifiers = {
    'isbn': '(1,7)',
    'issn': '(1,8)',
    'title': '(1,4)',
    'personalName': '(1,1)',
    'bib number': '(1,12)',
    'keyword': '(1,1016)'
}


def query(target=None, keyword=None, qualifier=qualifiers['keyword'],
          query_type='CCL'):

    if target is not None:
        host = target['host']
        database = target['database']
        port = target['port']
        syntax = target['syntax']
        user = target['user']
        password = target['password']

        try:
            if user is not None \
                    and password is not None:
                conn = zoom.Connection(
                    host, port,
                    user=user, password=password)
            else:
                conn = zoom.Connection(host, port)

            conn.databaseName = database
            conn.preferredRecordSyntax = syntax
            query_str = qualifier + '=' + keyword
            query = zoom.Query(query_type, query_str)
            res = conn.search(query)

            return (True, res)

        except zoom.ConnectionError:
            msg = (host, port, database, syntax, user)
            module_logger.exception('unreachable host: %s:%s@%s-%s,%s' % msg)
            return (False, None)
        except zoom.ClinetNotImplError:
            msg = (host, port, database, syntax, user)
            module_logger.exception(
                'unsupported request for: %s:%s@%s-%s,%s' % msg)
            return (False, None)
    else:
        return (False, None)
