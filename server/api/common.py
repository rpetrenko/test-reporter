# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import logging

from flask_restplus import Api
from server import settings
from bson import json_util
import json

log = logging.getLogger(__name__)

api = Api(version='1.0',
          title='Test Reporter API',
          description='API for test reporter')


@api.errorhandler
def default_error_handler(e):
    # message = 'An unhandled exception occurred.'
    log.exception(e)

    if not settings.FLASK_DEBUG:
        return {'message': str(e)}, 500


def db_response_to_json(x):
    json_str = json.dumps(x, default=json_util.default)
    return json.loads(json_str)


def jenkins_response_to_json(x):
    return json.loads(x)


def insert_creds_to_jenkins_url(username, api_key, uri):
    parts = uri.split("://")
    assert len(parts) == 2
    if api_key:
        insert_part = "{}:{}@".format(username, api_key)
    elif username:
        insert_part = "{}@".format(username)
    else:
        insert_part = ""
    uri = "{}://{}{}".format(parts[0], insert_part, parts[1])
    return uri


def create_jenkins_uri(username, api_key, uri):
    uri = insert_creds_to_jenkins_url(username, api_key, uri)
    if not uri.endswith('/'):
        uri = uri + '/'
    return "{}api/json".format(uri)
