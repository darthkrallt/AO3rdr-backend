import os
from flask import Flask, json, jsonify, abort, request, send_from_directory
from userlib import generator

app = Flask(__name__, static_url_path='')

@app.route('/static/<path:path>')
def static_page(path):
    return send_from_directory('static', path)


@app.route('/', methods=['GET'])
def redirect_to_index():
    return send_from_directory('static', 'index.html')


@app.route('/api/v1.0/user/<string:user_id>', methods=['GET'])
def user_exists(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    if not user:
        abort(404)
    return jsonify({'user_id': user})

# Technically, since we are CREATING a new user, this should be a POST, even
# though therere is no data being sent to do so.
@app.route('/api/v1.0/user', methods=['POST'])
def gen_user():
    gen = generator.Generator()
    user_id = gen.make_user()
    return jsonify({'user_id': user_id})


# NOTE: Don't want this implemented in production- test only!
@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['GET'])
def get_collection(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    if not user:
        abort(404)
    collection = {} # TODO: implement DB standardizer, merging
    # return jsonify({'collection': collection})

@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['POST'])
def merge_collection(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    if not user:
        abort(404)
    incomming_data = request.form.get('collection', {})
    collection = {} # TODO: implement DB standardizer, merging
    return jsonify({'collection': collection})