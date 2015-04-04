import os
import logging
from flask import Flask, json, jsonify, abort, request, send_from_directory, _app_ctx_stack
from userlib import generator
import merger.bulkmerge as bulkmerge
import merger.unitmerge as unitmerge
from database.dbconn import get_db, ItemNotFound
from userlib.reciever import validate_prefs, validate_work

import traceback
import sys


log = logging.getLogger(__name__)
logging.basicConfig()  # TODO consider file based config

app = Flask(__name__, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max upload of 5MB


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'db_conn'):
        log.debug('here')
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
    return jsonify({'user_id': user_id}), 201


# NOTE: Don't want this implemented in production- test only!
@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['GET'])
def get_collection(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    dbc = get_db()
    if not user:
        abort(404)

    collection = [_ for _ in dbc.get_all_works(user_id)]
    return jsonify({'collection': collection}), 200



@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['POST'])
def merge_collection(user_id):
    # if request.headers['Content-Type'] == 'application/json':
    #     incomming_data = request.json
    try:
        incomming_data = request.json
        log.debug('%r', incomming_data)
        validate_prefs(incomming_data)
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            abort(404)

        bm = bulkmerge.Merger()
        res = bm.merge(user_id, incomming_data['article_data'])

        to_db = []
        for k, v in res.whole.iteritems():
            v['work_id'] = k
            v['user_id'] = user_id
            to_db.append(v)

        # If all is well, save to DB
        try:
            db_conn = get_db()
        except:
            db_conn = DBconn()

        db_conn.batch_update(to_db)

        log.debug('%r %r', res.status_code,  res.remote)

        return jsonify({'diff': res.remote}), res.status_code
    except Exception as exc:
        log.debug('%r', traceback.print_exc())  # TODO use exc_info=True instead
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
    return jsonify({'work': work}), 200

@app.route('/api/v1.0/user/<string:user_id>/work/<string:work_id>', methods=['POST'])
def merge_work(user_id, work_id):
    # NOTE: if created, return 201
    # if request.headers['Content-Type'] == 'application/json':
    #     incomming_data = request.json
    try:
        incomming_data = request.json
        log.debug('%r', incomming_data)
        validate_work(incomming_data)
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            abort(404)

        um = unitmerge.Merger()
        res = um.merge(user_id, work_id, incomming_data)

        # If all is well, save to DB
        try:
            db_conn = get_db()
        except:
            db_conn = DBconn()

        try:
            db_conn.update_work(user_id, work_id, res.whole)
        except ItemNotFound:
            db_conn.create_work(user_id, work_id, res.whole)

        return jsonify({'diff': res.remote}), res.status_code
    except Exception as exc:
        log.debug('%r', traceback.print_exc())  # TODO use exc_info=True instead
        abort(400)  #Bad request
