# generates unique world languge order nubers
import datetime
import babelstore as db


def get_new_number():
    wlo_prefix = 'wlo'
    last_num = db.retrieve_last(db.UsedWlo)
    if last_num is None:
        wlo_num = str(1).zfill(10)
        new_id = wlo_prefix + wlo_num
    else:
        wlo_num = int(last_num.id[3:]) + 1
        wlo_num = str(wlo_num).zfill(10)
        new_id = wlo_prefix + wlo_num
    db.ignore_or_insert(
        db.UsedWlo,
        id=new_id,
        date=datetime.datetime.now())

    return new_id


def get_last_number():
    last_num = db.retrieve_last(db.UsedWlo)
    return last_num.id
