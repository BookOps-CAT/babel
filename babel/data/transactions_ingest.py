# datastore transaction of ImportView widget

from datetime import datetime
import logging
import sys

from sqlalchemy.inspection import inspect


from data.datastore import session_scope, Cart, Order, Resource
from data.datastore_worker import retrieve_record, insert
from errors import BabelError
from ingest.xlsx import ResourceDataReader
from logging_settings import format_traceback


mlogger = logging.getLogger('babel_logger')


def create_resource_reader(template_record, sheet_fh):
    record = template_record

    # convert any empty strings back to None
    state = inspect(record)
    for attr in state.attrs:
        if attr.loaded_value == '':
            setattr(record, attr.key, None)

    mlogger.debug('Applying following sheet template: {}'.format(record))

    try:

        reader = ResourceDataReader(
            sheet_fh,
            header_row=record.header_row,
            title_col=record.title_col,
            add_title_col=record.add_title_col,
            author_col=record.author_col,
            series_col=record.series_col,
            publisher_col=record.publisher_col,
            pub_date_col=record.pub_date_col,
            pub_place_col=record.pub_place_col,
            summary_col=record.summary_col,
            isbn_col=record.isbn_col,
            upc_col=record.upc_col,
            other_no_col=record.other_no_col,
            price_list_col=record.price_list_col,
            price_disc_col=record.price_disc_col,
            desc_url_col=record.desc_url_col,
            misc_col=record.misc_col)

        return reader

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            f'Unhandled on sheet reader. Traceback: {tb}')
        raise BabelError(exc)


def create_cart(
        cart_name, system_id, profile_id,
        resource_data, progbar):

    try:
        with session_scope() as session:

            # create Cart record
            name_exists = True
            n = 0
            while name_exists and n < 10:
                name_exists = retrieve_record(
                    session, Cart, name=cart_name)
                if name_exists:
                    n += 1
                    if '(' in cart_name:
                        end = cart_name.index('(')
                        cart_name = cart_name[:end]
                    cart_name = f'{cart_name}({n})'

            cart_rec = insert(
                session, Cart,
                name=cart_name,
                created=datetime.now(),
                updated=datetime.now(),
                system_id=system_id,
                user_id=profile_id)

            progbar['value'] += 1
            progbar.update()

            # create Resource records
            for d in resource_data:
                ord_rec = insert(
                    session, Order,
                    cart_id=cart_rec.did)

                insert(
                    session, Resource,
                    order_id=ord_rec.did,
                    title=d.title,
                    add_title=d.add_title,
                    author=d.author,
                    series=d.series,
                    publisher=d.publisher,
                    pub_date=d.pub_date,
                    pub_place=d.pub_place,
                    summary=d.summary,
                    isbn=d.isbn,
                    upc=d.upc,
                    other_no=d.other_no,
                    price_list=d.price_list,
                    price_disc=d.price_disc,
                    desc_url=d.desc_url,
                    misc=d.misc)

                progbar['value'] += 1
                progbar.update()

            session.flush()

            created_cart_id = cart_rec.did
            return created_cart_id

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            f'Unhandled on sheet ingest. Traceback: {tb}')
        raise BabelError(exc)
