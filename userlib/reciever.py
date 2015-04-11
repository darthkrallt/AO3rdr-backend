#!/usr/bin/env python

"""
   Userlib.reciever
        Accept incomming user data. QAQC.
"""

import re
import jsonschema

class InvalidStructure(Exception):
    pass

def user_valid(user_id):
    user_id = user_id.lower()
    prog = re.compile('(([0-9]|[a-z]){4,12}-{0,1}){1,7}')
    if prog.match(user_id):
        return user_id
    return ''


# Schema for a work
work_schema = {
    "$schema": "http://json-schema.org/schema#",

    "definitions": {
        "chapters": {
            "type": "object",
            "properties": {
                "published": {"type": "string"},  #Technically an int, but can be a "?"
                "total": {"type": "string"},
                "complete": {}, # Not a boolean
            },
            "required": ["published", "total"],
        },
    },

    "type": "object",

    "properties": {
        "chapters": {"$ref": "#/definitions/chapters"},
        "title": {"type": "string"},
        "hasupdate": {"type": "boolean"},
        "updated": {"type": "string"},  # unix timestamp
        "crawled": {"type": "string"},  # TZ
        "visit": {"type": "string"},  # TZ
        "author": {"type": "string"},
        "ao3id": {"type": "string"},  # Technically an int, stored as string
        "rating": {"type": "number"},
    },
    "required": ["chapters", "title", "ao3id"],
}

# User preferences schema
prefs_schema = {
    "$schema": "http://json-schema.org/schema#",

    "type": "object",
    "properties": {
        "tags": {
            "type": "array" # No max limit to tags
        },
        "autofilter": {"type": "boolean"}  #? is bool a thing for this?
    },
    #"required": [], # Nothing is required
}

# This is what gets passed in to 
collection_schema = {
    "$schema": "http://json-schema.org/schema#",

    "type": "object",
    "properties": {
        "user_id": {
            "type": "string",
            "pattern": "(([0-9]|[a-z]){4,12}-{0,1}){1,7}",
        },
        "article_data": { # The collection of works
            # Keyed by work_id, check seperately?
        },
        "prefs": prefs_schema,
    },
    #"required": ["user_id", "article_data", "prefs"],
    "additionalItems": False,
}

def validate_prefs(data):
    return jsonschema.validate(data, collection_schema)

def validate_work(data):
    return jsonschema.validate(data, work_schema)

# jsonschema.Draft4Validator.check_schema(schema)
# jsonschema.validate(dict_in, schema)

# NOTE: additionalItems does not work with "object"