#!/usr/bin/env python

"""
    merger.unitmerge.py
        Merge a user row and a database row together. Return the delta for each.
"""
import database.standardizer as dbs
import userlib.standardizer as uls
from database.dbconn import get_db
from standard import StandardObject

class Merger(object):
    def __init__(self):
        self.db_std = dbs.Standardizer()
        self.ul_std = uls.Standardizer()
        self.db_conn = get_db()

    def merge(self, db_in, remote_in):
        db_in = self.db_std.standardize(db_in)
        remote_in = self.ul_std.standardize(remote_in)
        new_object = db_in.merge(remote_in).format()
        self.db_conn.update_work(new_object['user_id'], new_object['work_id'], new_object)
