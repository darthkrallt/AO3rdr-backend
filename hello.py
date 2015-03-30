import os
from flask import Flask, json, jsonify, abort, request, send_from_directory, _app_ctx_stack
from userlib import generator
import merger.bulkmerge as bulkmerge
import merger.unitmerge as unitmerge
from database.dbconn import get_db

import traceback


app = Flask(__name__, static_url_path='')


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'db_conn'):
        print('here')
        top.db_conn.close()

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
    dbc = get_db()
    if not user:
        abort(404)

    collection = [_ for _ in dbc.get_all_works(user_id)]
    return jsonify({'collection': collection})



@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['POST'])
def merge_collection(user_id):
    if request.headers['Content-Type'] == 'application/json':
        incomming_data = request.json
    try:
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            abort(404)
        import sys
        print >> sys.stderr, incomming_data
        # TODO: sanatize incomming_data
        bm = bulkmerge.Merger()
        diff_db, diff_remote = bm.merge(incomming_data['collection'])
        return jsonify({'diff': diff_db})
    except Exception as exc:
        return repr(traceback.print_exc())
        abort(400)  #Bad request

# NOTE: Don't want this implemented in production- test only!
@app.route('/api/v1.0/user/<string:user_id>/work/<string:work_id>', methods=['GET'])
def get_work(user_id, work_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    dbc = get_db()
    if not user:
        abort(404)
    work = dbc.get_work(user_id , work_id) # TODO: implement DB standardizer, merging
    if not work:
        abort(204)
    return jsonify({'work': work})

@app.route('/api/v1.0/user/<string:user_id>/work/<string:work_id>', methods=['POST'])
def merge_work(user_id, work_id):
    # NOTE: if created, return 201
    if request.headers['Content-Type'] == 'application/json':
        incomming_data = request.json
    try:
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            abort(404)
        # TODO: sanatize incomming_data
        um = unitmerge.Merger()
        diff_db, diff_remote = um.merge(incomming_data["work"])
        return jsonify({'diff': diff_remote})
    except Exception as exc:
        return repr(traceback.print_exc())
        abort(400)  #Bad request
