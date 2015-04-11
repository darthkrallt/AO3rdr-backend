import os

import boto
from boto.dynamodb2.fields import GlobalAllIndex, HashKey, RangeKey
from boto.dynamodb2.items import Item
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table
from boto.dynamodb2.exceptions import ItemNotFound

from decimal import Decimal

from flask import _app_ctx_stack
import time


class DBconn(object):
    def __init__(self):
        aws_access_key_id = os.environ['S3_KEY']  # I AM OPS U NO GET MY KEYS
        aws_secret_access_key = os.environ['S3_SECRET']  # DIS IS MY JOB

        self._conn = DynamoDBConnection(
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key)
        self.works_table = Table('ao3rdr-works', connection=self._conn)
        self.immutable_fields = ['work_id', 'user_id']

    def get_user(self, user_id):
        res = self.works_table.query_2(
            user_id__eq=user_id, work_id__eq='settings', attributes=['user_id'])
        out = []
        for entry in res:
            out.append(self.serialize(entry)['user_id'])
        return out

    def add_user(self, user_id):
        """ Adding a user adds a special "work" which is used to store a user's
            settings.
        """
        return self.works_table.put_item(data={
            'user_id': user_id,
            'work_id': 'settings',
            'created': time.time()
        })

    def update_work(self, user_id, work_id, data):
        item = self.works_table.get_item(user_id=user_id, work_id=work_id)
        # update the item
        for key, value in data.iteritems():
            if key not in self.immutable_fields:
                item[key] = value
        item['updated'] = time.time()
        item.partial_save()

    def create_work(self, user_id, work_id, data):
        data['user_id'] = user_id
        data['work_id'] =  work_id
        self.works_table.put_item(data)

    def batch_update(self, data_list):
        with self.works_table.batch_write() as batch:
            for data in data_list:
                batch.put_item(data=data)

    def get_work(self, user_id, work_id):
        try:
            res = self.works_table.get_item(user_id=user_id, work_id=work_id)
        except ItemNotFound:
            return {}
        return self.serialize(res)

    def get_all_works(self, user_id):
        res = self.works_table.query_2(user_id__eq=user_id)
        for entry in res:
            yield self.serialize(entry)

    def close(self):
        self._conn.close()

    def serialize(self, item):
        out = serialize(dict(item))
        return out

def serialize(item):
    if isinstance(item, dict):
        out = {}
        for k, v in item.items():
            out[k] = serialize(v)
    elif isinstance(item, set) or isinstance(item, list):
        out = []
        for i in item:
            out.append(serialize(i))
    elif isinstance(item, Decimal):
        out = float(item)
    else:
        out = item
    return out


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'db_conn'):
        top.__setattr__('db_conn', DBconn())
    return top.db_conn


'''
# Tips for working with DynameDB
works_table = Table('ao3rdr-works', connection=conn)
# put_item has param overwrite=False
test_data = {
    'user_id': 'testuser',
    'work_id': '123456',
    'rating': 5
}
works_table.put_item(test_data)
# When using get item, must use both primary and secondary keys
works_table.get_item(user_id='testuser', work_id='123456')

# To get by user, query is OK
res = works_table.query_2(user_id__eq='testuser')
for entry in res:
    print entry
# entry useful fields: _data, keys(), and index like a dict, eg entry['work_id']

# Use the secondary index
res = works_table.query_2(rating__eq=5, index='rating-index')
for entry in res:
    print entry['work_id']

# get_item(table_name, key, attributes_to_get=None, consistent_read=False, object_hook=None)
# put_item(table_name, item, expected=None, return_values=None, object_hook=None)
'''
