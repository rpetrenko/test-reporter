# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

from flask_restplus import Resource
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsData
import json

ns = api.namespace('jenkins/data', description='Jenkins data for jobs, builds, test results')


class DataBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsData()
        super(DataBase, self).__init__(api, args, kwargs)


@ns.route('/')
class Datas(DataBase):
    def get(self):
        return db_response_to_json(self.model.get_doc())


@ns.route('/<string:doc_id>')
@api.response(404, 'Job not found.')
class Data(DataBase):

    def get(self, doc_id):
        x = self.model.get_doc(doc_id=doc_id)
        if x:
            x = db_response_to_json(x)
            x['data'] = json.loads(x['data'])
        return x, x and 200 or 404



