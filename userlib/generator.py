#!/usr/bin/env python

"""
   Userlib.generator
        Generate new user that does not already exist in the DB.
"""

import uuid

class Generator(object):
    def __init__(self):
        # connect to DB
        pass
        # testing junk
        self.users = ['testuser', 'alice', 'bob']

    def make_user(self):
        # TODO: check this against DB
        return uuid.uuid4()

    def user_exists(self, user_id):
        # testing junk
        if user_id in self.users:
            return user_id