#!/usr/bin/env python

"""
    merger.unitmerge.py
        Merge a user row and a database row together. Return the delta for each.
"""
import database.standardizer as dbs
import userlib.standardizer as uls
from collections import namedtuple
from database.dbconn import get_db, DBconn
from standard import StandardObject

class Merger(object):
    out = namedtuple('MergeRes', ['db', 'remote', 'whole'])
    def __init__(self):
        self.db_std = dbs.Standardizer()
        self.ul_std = uls.Standardizer()
        # NOTE this only fails in dev outside of flask.
        try:
            self.db_conn = get_db()
        except:
            self.db_conn = DBconn()

    def merge(self, user_id, work_id, remote_in):
        db_in = self.db_conn.get_work(user_id, work_id)
        db_in = self.db_std.standardize(db_in)
        remote_in = self.ul_std.standardize(remote_in)
        new_object = db_in.merge(remote_in)
        new_dict = new_object.format()

        out = self.out(
            db=db_in.diff(new_object).format(),
            remote= remote_in.diff(new_object).format(),
            whole=new_object.format()
        )
        return out
