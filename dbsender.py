import os

import boto
from boto.dynamodb2.fields import GlobalAllIndex, HashKey, RangeKey
from boto.dynamodb2.items import Item
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table


class dbsender(object):
    def __init__(self):
        aws_access_key_id = os.environ['S3_KEY']  # I AM OPS U NO GET MY KEYS
        aws_secret_access_key = os.environ['S3_SECRET']  # DIS IS MY JOB

        self._conn = DynamoDBConnection(
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key)
        self.works_table = Table('ao3rdr-works', connection=self._conn)
        self.immutable_fields = ['work_id', 'user_id']

    def get_user(self, user_id):
        res = self.works_table.query_2(user_id__eq='testuser')
        out = []
        for entry in res:
            out.append(entry._data)
        return out

    def update_work(user_id, work_id, data):
        item = self.works_table.get_item(user_id=user_id, work_id=work_id)
        # update the item
        for key, value in data:
            if key not in self.immutable_fields:
                item[key] = value
        item.put()


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
