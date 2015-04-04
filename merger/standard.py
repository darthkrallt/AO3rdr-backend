#!/usr/bin/env python

"""
    merger.standard
        Standard object
"""

from collections import namedtuple


MERGER_RESPONSE = namedtuple('MergeRes', ['db', 'remote', 'whole', 'status_code'])

TS_STR = '__ts'

class StandardObject(object):
    _ts_str = TS_STR
    _default_time = 0

    def __init__(self, data_objects=None, timestamp_objects=None):
        self._data = data_objects if data_objects else {}
        self._timestamps = timestamp_objects if timestamp_objects else {}

    def __getitem__(self, key):
        data = self._data[key]
        timestamp = self._timestamps.get(
            self.key_to_ts(key), self._default_time)
        return {key: data, 'timestamp': timestamp}

    def __contains__(self, key):
        if key in self._data:
            return True
        return False

    def get(self, key, alt=None):
        if key in self:
            return self[key]
        return alt

    def get_ts(self, key):
        ts_key = self.key_to_ts(key)
        if key in self._data.keys():
            return self[key]['timestamp']
        return None

    def set_item(self, key, value, timestamp=None):
        self._data[key] = value
        if timestamp > self._default_time:
            self._timestamps[self.key_to_ts(key)] = timestamp

    def __iter__(self):
        for x in self._data:
            yield x, self[x]
        raise StopIteration

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def key_to_ts(self, key):
        return '{0}{1}'.format(key,  self._ts_str)

    def merge(self, remote_in):
        out = StandardObject()
        for key in set(self.keys() + remote_in.keys()):
            db_ts = self.get_ts(key)
            ul_ts = remote_in.get_ts(key)
            if db_ts > ul_ts:
                data = self[key]
            else:
                data = remote_in[key]
            out.set_item(key, data[key], data['timestamp'])
        return out

    def diff(self, remote_in):
        out = StandardObject()
        for key in set(self.keys() + remote_in.keys()):
            db_ts = self.get_ts(key)
            ul_ts = remote_in.get_ts(key)
            if db_ts > ul_ts:
                data = self[key]
                data_old = remote_in.get(key)
            else:
                data = remote_in[key]
                data_old = self.get(key)
            if data != data_old:
                out.set_item(key, data[key], data['timestamp'])
        return out

    def format(self):
        out = self._data.copy()
        out.update(self._timestamps)
        return out

    def __str__(self):
        return str(self.format())


class Standardizer(object):
    def __init__(self):
        self.exclude = []

    # Currently does nothing :P
    def standardize(self, db_in):
        timestamps = {}
        data = {}
        for key, value in db_in.iteritems():
            if key not in self.exclude:
                if key.endswith(TS_STR):
                    timestamps[key] = value
                else:
                    data[key] = value

        return StandardObject(data, timestamps)