# Supports datastore transations on GridView
import logging

from sqlalchemy.exc import IntegrityError, InternalError


from errors import BabelError
from data.datastore import session_scope, DistGrid, GridLocation
from data.datastore_worker import insert, update_record
from gui.utils import get_id_from_index


mlogger = logging.getLogger('babel_logger')


def save_grid_data(**kwargs):
    """
    used in GridView
    """
    locs = []
    for loc in kwargs['gridlocs']:
        branch_id = get_id_from_index(loc['branch'], kwargs['branch_idx'])
        shelf_id = get_id_from_index(loc['shelf'], kwargs['shelf_idx'])
        if loc['gridloc_id']:
            locs.append(
                GridLocation(
                    did=loc['gridloc_id'],
                    distgrid_id=loc['distgrid_id'],
                    branch_id=branch_id,
                    shelfcode_id=shelf_id,
                    qty=loc['qty']))
        else:
            if loc['distgrid_id']:
                locs.append(
                    GridLocation(
                        distgrid_id=loc['distgrid_id'],
                        branch_id=branch_id,
                        shelfcode_id=shelf_id,
                        qty=loc['qty']
                    ))
            else:
                locs.append(
                    GridLocation(
                        branch_id=branch_id,
                        shelfcode_id=shelf_id,
                        qty=loc['qty']
                    ))

    with session_scope() as session:
        try:
            if kwargs['grid_did']:
                update_record(
                    session,
                    DistGrid,
                    kwargs['grid_did'],
                    name=kwargs['name'],
                    distset_id=kwargs['distset_id'],
                    gridlocations=locs)
            else:
                insert(
                    session,
                    DistGrid,
                    name=kwargs['name'],
                    distset_id=kwargs['distset_id'],
                    gridlocations=locs)
        except IntegrityError as e:
            raise BabelError(e)
        except InternalError as e:
            raise BabelError(e)


def copy_grid_data(grid_record):
    mlogger.debug('Copying grid record did={}, name={}'.format(
        grid_record.did, grid_record.name))


def copy_distribution_data():
    pass
