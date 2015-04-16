#!/usr/bin/env python

"""
    merger.standardizer
        Take the data from the database.sender and standardize its format.
"""
import merger.standard


class Standardizer(merger.standard.Standardizer):
    def __init__(self):
        super(Standardizer, self).__init__()
        self.exclude = ['created', 'work_id', 'user_id', 'db_updated']
