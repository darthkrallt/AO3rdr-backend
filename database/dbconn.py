import os
import time

from decimal import Decimal
import json

from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table
from boto.dynamodb2.exceptions import ItemNotFound

import boto3

#from flask import g


class DBconn(object):
    def __init__(self):
        aws_access_key_id = os.environ.get('S3_KEY', None)  # I AM OPS U NO GET MY KEYS
        aws_secret_access_key = os.environ.get('S3_SECRET', None)  # DIS IS MY JOB

        session = boto3.Session(
            region_name='us-east-1',
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key,
        )

        ddb = session.resource('dynamodb')

        self.works_table = ddb.Table('ao3rdr-works2')
        self.immutable_fields = ['work_id', 'user_id']

    def get_user(self, user_id):
        res = self.works_table.get_item(
            Key={'user_id':user_id, 'work_id':'settings'},
            AttributesToGet=['user_id']
        )
        return res.get('Item', {}).get('user_id')

    def add_user(self, user_id):
        """ Adding a user adds a special "work" which is used to store a user's
            settings.
        """
        item = {
            'user_id': user_id,
            'work_id': 'settings',
            'created': time.time(),
        }
        item = json.loads(json.dumps(item), parse_float=Decimal)

        return self.works_table.put_item(Item=item)

    def create_work(self, user_id, work_id, data):
        data['user_id'] = user_id
        data['work_id'] =  work_id
        if 'created' not in data:
            data['created'] = time.time()

        item = json.loads(json.dumps(data), parse_float=Decimal)
        self.works_table.put_item(Item=item)

    def get_work(self, user_id, work_id):
        res = self.works_table.get_item(Key={'user_id':user_id, 'work_id':work_id})
        return self.serialize(res.get('Item', {}))

    def update_work(self, user_id, work_id, data):
        item = self.get_work(user_id=user_id, work_id=work_id)
        # update the item
        for key, value in data.items():
            if key not in self.immutable_fields:
                item[key] = value
        item['db_updated'] = time.time()

        # Using put_item because the UpdateExpression looks too finicky
        self.works_table.put_item(
            Item=json.loads(json.dumps(item), parse_float=Decimal)
        )

    # HERE - resume updating


    def batch_update(self, data_list):
        with self.works_table.batch_write() as batch:
            for data in data_list:
                batch.put_item(data=data)

    def get_all_works(self, user_id):
        res = self.works_table.query_2(user_id__eq=user_id)
        for entry in res:
            yield self.serialize(entry)

    def serialize(self, item):
        out = serialize(dict(item))
        return out

def serialize(item):
    if isinstance(item, dict):
        out = {}
        for k, v in list(item.items()):
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
    if 'db_conn' not in g:
        g.db_conn = DBconn()

    return g.db_conn


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
