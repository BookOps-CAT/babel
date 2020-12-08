# -*- coding: utf-8 -*-

import unittest


from .context import datastore, datastore_worker


class TestDataPopulation(unittest.TestCase):
    """creates test data in datastore"""

    def setUp(self):
        with datastore.session_scope() as session:
            datastore_worker.insert_or_ignore(
                session, datastore.User, name="Tomek", bpl_code="t", nyp_code="k"
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.Vendor,
                name="China Books",
                bpl_code="chbks",
                nyp_code="cbks",
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="world lang",
                system_id=1,
                code="wl",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="fiction",
                system_id=1,
                code="fc",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="non-fic",
                system_id=1,
                code="fn",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="NONE",
                system_id=1,
                code=None,
                includes_audn=False,
            )
            # datastore_worker.insert_or_ignore(session, datastore.ShelfCode, name='childrens place', system_id=1, code='jcp', includes_audn=False)
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="world lang",
                system_id=2,
                code="0l",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="fiction",
                system_id=2,
                code="0f",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="non-fic",
                system_id=2,
                code="0n",
                includes_audn=True,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.ShelfCode,
                name="NONE",
                system_id=2,
                code=None,
                includes_audn=False,
            )

            session.commit()

            distset = datastore_worker.insert_or_ignore(
                session, datastore.DistSet, name="test distr.", system_id=1, user_id=2
            )
            session.commit()
            distgrid = datastore_worker.insert_or_ignore(
                session, datastore.DistGrid, name="grid A", distset_id=distset.did
            )
            session.commit()
            datastore_worker.insert_or_ignore(
                session,
                datastore.GridLocation,
                distgrid_id=distgrid.did,
                branch_id=11,
                shelfcode_id=1,
                qty=2,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.GridLocation,
                distgrid_id=distgrid.did,
                branch_id=12,
                shelfcode_id=1,
                qty=1,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.GridLocation,
                distgrid_id=distgrid.did,
                branch_id=13,
                shelfcode_id=2,
                qty=3,
            )

            distgrid = datastore_worker.insert_or_ignore(
                session, datastore.DistGrid, name="grid B", distset_id=distset.did
            )
            session.commit()
            datastore_worker.insert_or_ignore(
                session,
                datastore.GridLocation,
                distgrid_id=distgrid.did,
                branch_id=12,
                shelfcode_id=1,
                qty=2,
            )
            datastore_worker.insert_or_ignore(
                session,
                datastore.GridLocation,
                distgrid_id=distgrid.did,
                branch_id=13,
                shelfcode_id=1,
                qty=1,
            )

    def test_start(self):
        pass


if __name__ == "__main__":
    unittest.main()
