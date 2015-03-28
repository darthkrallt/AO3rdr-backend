#!/usr/bin/env python

"""
   Userlib.reciever
        Accept incomming user data. QAQC.
"""

import re

def user_valid(user_id):
    user_id = user_id.lower()
    prog = re.compile('(([0-9]|[a-z]){4,12}-{0,1}){1,7}')
    if prog.match(user_id):
        return user_id
    return ''