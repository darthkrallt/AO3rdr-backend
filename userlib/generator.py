#!/usr/bin/env python

"""
   Userlib.generator
        Generate new user that does not already exist in the DB.
"""

from flask import _app_ctx_stack
from database.dbconn import get_db
import uuid

class Generator(object):
    def __init__(self):
        # connect to DB
        self.db_conn = get_db()
        # testing junk
        self.users = ['testuser', 'alice', 'bob']

    def make_user(self):
        # TODO: retry on collision
        user_id = str(uuid.uuid4()).lower()
        assert not self.user_exists(user_id)
        self.db_conn.add_user(user_id)
        return user_id

    def user_exists(self, user_id):
        # testing junk
        if user_id.lower() in self.db_conn.get_user(user_id):
            return user_id