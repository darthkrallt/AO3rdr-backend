#!/usr/bin/env python

"""
    merger.bulkmerge
        Take in all user data and all matching DB data. Join the two, then
        return the two deltas.
"""
import database.standardizer as dbs
import userlib.standardizer as uls
from database.dbconn import get_db, DBconn
from standard import StandardObject

class Merger(object):
    def __init__(self):
        self.db_std = dbs.Standardizer()
        self.ul_std = uls.Standardizer()
        # NOTE this only fails in dev outside of flask.
        try:
            self.db_conn = get_db()
        except:
            self.db_conn = DBconn()

    def merge(self, remote_in):
        db_in = self.db_conn.get_all_works(remote_in[0]['user_id'])

        db_in = {_['work_id']: self.db_std.standardize(_) for _ in db_in}
        remote_in = {
            _['work_id']: self.db_std.standardize(_) for _ in remote_in}

        diff_db = []
        diff_remote = []
        new_objects = []

        for work_id in set(db_in.keys() + remote_in.keys()):
            dbw = db_in.get(work_id, StandardObject())
            rmw = remote_in.get(work_id, StandardObject())
            new_object = dbw.merge(rmw)

            diff_db.append(dbw.diff(new_object).format())
            diff_remote.append(rmw.diff(new_object).format())

            # If there have been changes to the DB object, we want to save it.
            if dbw.format():
                new_objects.append(new_object.format())

        # UPDATE BULK
        self.db_conn.batch_update(new_objects)

        # TODO: these diffs need their ID's!
        return diff_db, diff_remote
