# Supports datastore transations on GridView
import logging
import sys

from sqlalchemy.exc import IntegrityError, InternalError


from errors import BabelError
from data.datastore import (session_scope, DistGrid, DistSet,
                            GridLocation)
from data.datastore_worker import (insert, update_record,
                                   retrieve_record)
from gui.utils import get_id_from_index
from logging_settings import format_traceback


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
    mlogger.debug(
        f'Copying grid record did={grid_record.did}, name={grid_record.name}')
    try:
        with session_scope() as session:
            # create new name
            # check if used and adjust
            exists = True
            n = 0
            while exists:
                new_name = f'{grid_record.name}-copy({n})'
                rec = retrieve_record(
                    session, DistGrid,
                    distset_id=grid_record.distset_id,
                    name=new_name)
                if not rec:
                    exists = False
                n += 1

            # compile location data
            locs = []
            for loc in grid_record.gridlocations:
                locs.append(
                    GridLocation(
                        branch_id=loc.branch_id,
                        shelfcode_id=loc.shelfcode_id,
                        qty=loc.qty))

            # # insert to datastore
            rec = insert(
                session, DistGrid,
                distset_id=grid_record.distset_id,
                name=new_name,
                gridlocations=locs)

            mlogger.debug(
                f'New DistGrid record added: {rec}')

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            f'Unhandled error while using ResourceDataReader.'
            'Traceback: {tb}')
        raise BabelError(exc)


def copy_distribution_data(distr_record, user_id):

    with session_scope() as session:
        # create new name
        # check if used and adjust
        exists = True
        n = 0
        while exists:
            new_name = f'{distr_record.name}-copy({n})'
            rec = retrieve_record(
                session, DistSet,
                name=new_name,
                user_id=user_id,
                system_id=distr_record.system_id)
            if not rec:
                exists = False
            n += 1

        # prep copy of distrgrids & gridlocations
        grids = []
        for grid in distr_record.distgrids:
            locs = []
            for loc in grid.gridlocations:
                locs.append(
                    GridLocation(
                        branch_id=loc.branch_id,
                        shelfcode_id=loc.shelfcode_id,
                        qty=loc.qty))
            grids.append(
                DistGrid(
                    name=grid.name,
                    gridlocations=locs))

        rec = insert(
            session,
            DistSet,
            name=new_name,
            system_id=distr_record.system_id,
            user_id=user_id,
            distgrids=grids)

        mlogger.debug(f'New DistSet added: {rec}')
