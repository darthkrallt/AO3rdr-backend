import unittest

import boto3
from moto import mock_dynamodb

from dbconn import DBconn
from unittest import mock


class TestDBconn(unittest.TestCase):

    maxDiff = None

    @classmethod
    @mock_dynamodb
    def ddbSetup(cls):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table_name = 'ao3rdr-works2'
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id','KeyType': 'HASH'}, # Partition
                {'AttributeName': 'work_id','KeyType': 'RANGE'}, # Sort
            ],

            AttributeDefinitions=[
                {'AttributeName': 'user_id','AttributeType': 'S'},
                {'AttributeName': 'work_id','AttributeType': 'S'},
            ],

            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'work_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'work_id',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': [
                            'user_id',
                        ]
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 123
                    }
                },
            ],

            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10,
            }
        )

    @mock_dynamodb
    @mock.patch('time.time', mock.MagicMock(return_value=1662866828.6330128))
    def test_create_user(self):
        self.ddbSetup()
        user_id = 'testuser'
        conn = DBconn()
        conn.add_user(user_id)
        res = conn.get_user(user_id)
        self.assertEqual(res, user_id)

    @mock_dynamodb
    @mock.patch('time.time', mock.MagicMock(return_value=1662866828.6330128))
    def test_create_work(self):
        self.ddbSetup()
        user_id = 'testuser'
        work_id = '2778923'

        test_work = {
          "ao3id": work_id,
          "author": "uraneia",
          "author__ts": "1467868047.7049999237060546875",
          "chapters": {
              "complete": 1,
              "published": 1,
              "total": 1,
          },
          "chapters__ts": "1467868047.7049999237060546875",
          "rating":  "5",
          "rating__ts": "1467868047.7049999237060546875",
          "title":  "sing each song twice over",
          "title__ts": "1467868047.7049999237060546875",
        }

        conn = DBconn()
        conn.create_work(user_id, work_id, test_work)

        res = conn.get_work(user_id, work_id)
        self.assertEqual(res, test_work)


    @mock_dynamodb
    @mock.patch('time.time', mock.MagicMock(return_value=1662866828.6330128))
    def test_get_work_404(self):
        self.ddbSetup()
        user_id = 'testuser'
        work_id = '2778923'

        conn = DBconn()

        res = conn.get_work(user_id, work_id)
        self.assertEqual(res, {})


    @mock_dynamodb
    @mock.patch('time.time', mock.MagicMock(return_value=1662866828.6330128))
    def test_update_work(self):
        self.ddbSetup()
        user_id = 'testuser'
        work_id = '2778923'

        test_work = {
          "user_id": user_id,
          "work_id": work_id,
          "ao3id": work_id,
          "author": "uraneia",
          "author__ts": 1467868047.7049999237060546875,
          "chapters": {
              "complete": 1,
              "published": 1,
              "total": 1,
          },
          "chapters__ts": 1467868047.7049999237060546875,
          "created": 1467868047.7049999237060546875,
          "db_updated": 1467868047.7049999237060546875,
          "rating":  5,
          "rating__ts": 1467868047.7049999237060546875,
          "title":  "sing each song twice over",
          "title__ts": 1467868047.7049999237060546875,
        }

        update_data = {"rating": 3, "rating__ts": 1662866828.6330128}

        conn = DBconn()
        conn.create_work(user_id, work_id, test_work)

        conn.update_work(user_id, work_id, update_data)


        updated_work = {
          "user_id": user_id,
          "work_id": work_id,
          "ao3id": work_id,
          "author": "uraneia",
          "author__ts": 1467868047.7049999237060546875,
          "chapters": {
              "complete": 1.0,
              "published": 1.0,
              "total": 1.0,
          },
          "chapters__ts": 1467868047.7049999237060546875,
          "created": 1467868047.7049999237060546875,
          "db_updated": 1662866828.6330128,
          "rating":  3.0,
          "rating__ts": 1662866828.6330128,
          "title":  "sing each song twice over",
          "title__ts": 1467868047.7049999237060546875,
        }
        res = conn.get_work(user_id, work_id)
        self.assertEqual(res, updated_work)

    @mock_dynamodb
    @mock.patch('time.time', mock.MagicMock(return_value=1662866828.6330128))
    def test_batch(self):
        self.ddbSetup()
        user_id = 'testuser'

        test_work1 = {
          "user_id": user_id,
          "work_id": '2778923',
          "chapters": {
              "complete": 1.0,
              "published": 1.0,
              "total": 1.0,
          },
          "chapters__ts": 1467868047.7049999237060546875,
        }

        test_work1_update_data = {"user_id": user_id, "work_id": '2778923', "rating": 3.0, "rating__ts": 1662866828.6330128}

        test_work2_brand_new = {
            "user_id": user_id,
            "work_id": '1234',
            "chapters": {
                "complete": 0.0,
                "published": 1.0,
                "total": "?",
            },
            "chapters__ts": 1467868047.7049999237060546875,
        }

        conn = DBconn()
        conn.create_work(user_id, test_work1['work_id'], test_work1)


        test_work1.update(test_work1_update_data)
        conn.batch_update([test_work1, test_work2_brand_new])

        res = [_ for _ in conn.get_all_works(user_id)]
        res.sort(key=lambda x: x['work_id'])

        self.assertEqual([test_work2_brand_new, test_work1], res)



if __name__ == '__main__':
    unittest.main()