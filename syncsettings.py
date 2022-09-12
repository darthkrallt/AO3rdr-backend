from flask import Flask, jsonify, abort, request, send_from_directory, g
import logging
import re

from database.dbconn import get_db, DBconn, ItemNotFoundError
from merger import bulkmerge as bulkmerge
from merger import unitmerge as unitmerge
from userlib import generator
from userlib.reciever import validate_collection, validate_work



log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # TODO consider file based config

app = Flask(__name__, static_url_path='', instance_relative_config=True)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max upload of 5MB


@app.errorhandler(404)
def not_found(error=None):
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    db = g.pop('db_conn', None)
    if db is not None:
        db.close()

@app.route('/static/<path:path>')
def static_page(path):
    return send_from_directory('static', path)


@app.route('/', methods=['GET'])
def redirect_to_index():
    return send_from_directory('static', 'index.html')


@app.route('/api/v1.0/status', methods=['GET'])
def heartbeat():
    return jsonify({'status': 'online'}), 200


@app.route('/api/v1.0/hellobar', methods=['GET'])
def hellobar():
    contents = {
        'created_at': 1662956168.0,
        'expires_at': 1665634539.0,
        'text': """
        <p>
            AO3rdr version 2.0 ~news~ 2022-09-11
        </p>
        <p>
            Dusting the cobwebs off this extension to restore functionality. The domain was poached, so we are moving to ao3rdr.org, overhauled the backend, and some minor changes to the frontend. Enjoy.
        </p>""",
    }
    return jsonify(contents)

@app.route('/api/v1.0/user/<string:user_id>', methods=['GET'])
def user_exists(user_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    if not user:
        return not_found()
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
        return not_found()

    collection = [_ for _ in dbc.get_all_works(user_id)]
    return jsonify({'collection': collection}), 200


# TODO: This is a temporary fix to get the error rate back down
def work_id_is_valid(work_id):
    """Work ids are a string of numbers"""
    return re.match(r'^[0-9]+$', work_id)


@app.route('/api/v1.0/user/<string:user_id>/collection', methods=['POST'])
def merge_collection(user_id):
    # if request.headers['Content-Type'] != 'application/json':
    #     abort(400)
    try:
        incomming_data = request.json
        log.info('%r', incomming_data)
        validate_collection(incomming_data)
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            return not_found()

        bm = bulkmerge.Merger()
        res = bm.merge(user_id, incomming_data['article_data'])

        to_db = []
        for k, v in res.whole.items():
            v['work_id'] = k
            v['user_id'] = user_id
            if not work_id_is_valid(k):
                print('Invalid work_id %s' % k)
                continue
            to_db.append(v)

        # If all is well, save to DB
        try:
            db_conn = get_db()
        except:
            db_conn = DBconn()

        db_conn.batch_update(to_db)

        log.info('%r %r', res.status_code,  res.remote)

        return jsonify({'diff': res.remote}), res.status_code
    except Exception:
        log.error('Error in merge_collection')
        abort(400)  #Bad request

# NOTE: Don't want this implemented in production- test only!
@app.route('/api/v1.0/user/<string:user_id>/work/<string:work_id>', methods=['GET'])
def get_work(user_id, work_id):
    gen = generator.Generator()
    user = gen.user_exists(user_id)
    dbc = get_db()
    if not user:
        return not_found()
    work = dbc.get_work(user_id , work_id) # TODO: implement DB standardizer, merging
    if not work:
        return not_found()
    return jsonify({'work': work}), 200

@app.route('/api/v1.0/user/<string:user_id>/work/<string:work_id>', methods=['POST'])
def merge_work(user_id, work_id):
    # if request.headers['Content-Type'] != 'application/json':
    #     abort(400)
    try:
        incomming_data = request.json
        log.info('%r', incomming_data)

        if (not work_id) or (work_id == 'undefined'):
            return not_found()


        validate_work(incomming_data)
        gen = generator.Generator()
        user = gen.user_exists(user_id)
        if not user:
            return not_found()

        um = unitmerge.Merger()
        res = um.merge(user_id, work_id, incomming_data)

        # If all is well, save to DB
        try:
            db_conn = get_db()
        except:
            db_conn = DBconn()

        try:
            db_conn.update_work(user_id, work_id, res.whole)
        except ItemNotFoundError:
            db_conn.create_work(user_id, work_id, res.whole)

        return jsonify({'diff': res.remote}), res.status_code
    except Exception:
        log.error('Error in merge_work')  # TODO use exc_info=True instead
        abort(400)  #Bad request
