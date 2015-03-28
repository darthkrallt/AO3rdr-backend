#!/usr/bin/env python

"""
    merger.unitmerge.py
        Merge a user row and a database row together. Return the delta for each.
"""
import database.standardizer as dbs
import userlib.standardizer as uls
from standard import StandardObject

class Merger(object):
    def __init__(self):
        self.db_std = dbs.Standardizer()
        self.ul_std = uls.Standardizer()

    def merge(self, db_in, remote_in):
        out = StandardObject()
        db_in = self.db_std.standardize(db_in)
        remote_in = self.ul_std.standardize(remote_in)
        for key in set(db_in.keys() + remote_in.keys()):
            db_ts = db_in.get_ts(key)
            ul_ts = remote_in.get_ts(key)
            if db_ts > ul_ts:
                data = db_in[key]
            else:
                data = remote_in[key]
            out.set_item(key, data[key], data['timestamp'])
        return out

