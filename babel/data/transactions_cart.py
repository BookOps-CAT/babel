import logging


from errors import BabelError
from data.datastore import session_scope, DistSet, DistGrid, GridLocation
from data.datastore_worker import (insert_or_ignore, insert, update_record,
                                   retrieve_record)
from gui.utils import get_id_from_index


mlogger = logging.getLogger('babel_logger')


def save_new_dist_and_grid(
        system_id, profile_id, grids,
        branch_idx, shelf_idx,
        dist=None, grid=None):
    """
    args:
        system_id: int, did from System table
        profile_id: int, did from User table
        grids: dict, grids element of CartView tracker
        dist: str, name of the new DistSet record
        grid: str, name of the new DistGrid record
    """
    try:
        mlogger.debug(
            'Creating new dist/grid from CartView. '
            f'system: {system_id}, profile: {profile_id}, '
            f'dist: {dist}, grid: {grid}')

        if profile_id is not None:
            with session_scope() as session:
                dist_rec = insert_or_ignore(
                    session,
                    DistSet,
                    system_id=system_id,
                    user_id=profile_id,
                    name=dist)
                mlogger.debug(f'dist_rec: {dist_rec}')

                # check if given grid already exists
                grid_rec = retrieve_record(
                    session, DistGrid, name=grid, distset_id=dist_rec.did)
                mlogger.debug(f'grid_rec: {grid_rec}')

                # determine new gridLocations
                locations = []
                locs = grids['locs']
                for l in locs:
                    if grid_rec:
                        locations.append(
                            GridLocation(
                                distgrid_id=grid_rec.did,
                                branch_id=get_id_from_index(
                                    l['branchCbx'].get(), branch_idx),
                                shelfcode_id=get_id_from_index(
                                    l['shelfCbx'].get(), shelf_idx),
                                qty=int(l['qtyEnt'].get())))
                    else:
                        locations.append(
                            GridLocation(
                                branch_id=get_id_from_index(
                                    l['branchCbx'].get(), branch_idx),
                                shelfcode_id=get_id_from_index(
                                    l['shelfCbx'].get(), shelf_idx),
                                qty=int(l['qtyEnt'].get())))
                mlogger.debug(f'New locations: {locations}')

                if grid_rec:
                    mlogger.debug('Updating existing grid_rec.')
                    update_record(
                        session,
                        DistGrid,
                        grid_rec.did,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations)
                else:
                    mlogger.debug('Inserting new grid_rec.')
                    insert(
                        session,
                        DistGrid,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations)

    except ValueError as e:
        mlogger.error(
            'User attempted to save new grid with incorrect values.'
            f'Error: {e}')
        raise BabelError(
            'Your new grid includes invalid values.\n'
            'Please make sure branch, shelf, and qty are valid.')
