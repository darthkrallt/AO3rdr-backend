#!/usr/bin/env python

"""
    merger.bulkmerge
        Take in all user data and all matching DB data. Join the two, then
        return the two deltas.
"""
import database.standardizer as dbs
import userlib.standardizer as uls
from collections import namedtuple
from database.dbconn import get_db, DBconn
from standard import StandardObject, MERGER_RESPONSE

class Merger(object):

    def __init__(self):
        self.db_std = dbs.Standardizer()
        self.ul_std = uls.Standardizer()
        # NOTE this only fails in dev outside of flask.
        try:
            self.db_conn = get_db()
        except:
            self.db_conn = DBconn()

    def merge(self, user_id, remote_in):
        """ Takes in a dict
            {
                "workd_id1: {...work dict 1...},
                "workd_id2: {...work dict 2...},
            }
        """
        db_in = self.db_conn.get_all_works(user_id)

        db_in = {_['work_id']: self.db_std.standardize(_) for _ in db_in}
        remote_in = {k: self.db_std.standardize(v) for k, v in remote_in.iteritems()}

        diff_db = {}
        diff_remote = {}
        new_objects = {}

        for work_id in set(db_in.keys() + remote_in.keys()):
            dbw = db_in.get(work_id, StandardObject())
            rmw = remote_in.get(work_id, StandardObject())
            new_object = dbw.merge(rmw)

            diff_db[work_id] = dbw.diff(new_object).format()
            diff_remote[work_id] = rmw.diff(new_object).format()

            # If there have been changes to the DB object, we want to save it.
            if diff_db[work_id]:
                new_objects[work_id] = new_object.format()

        status_code = 204  # The server has fulfilled the request but does not
        # need to return an entity-body.
        for k, v in diff_remote.iteritems():
            if v:
                status_code = 205 # The server has fulfilled the request and
                break
        # the user agent SHOULD reset the document view.

        out = MERGER_RESPONSE(
            db=diff_db,
            remote=diff_remote,
            whole=new_objects,
            status_code=status_code
        )
        return out
