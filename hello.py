import os
from flask import Flask, jsonify, abort
from userlib import generator

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/todo/api/v1.0/user_exists/<string:user_id>', methods=['GET'])
def user_exists(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    if not user:
        abort(404)
    return jsonify({'user_id': user})

@app.route('/todo/api/v1.0/user', methods=['GET'])
def gen_user():
    gen = generator.Generator()
    user_id = gen.make_user()
    return jsonify({'user_id': user_id})

