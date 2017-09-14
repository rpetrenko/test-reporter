# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

from flask import request
from flask_restplus import Resource
from server.api.jenkins.serializers import label_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsLabels


ns = api.namespace('jenkins/labels', description='Labels used to group test results in reports')


class LabelBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsLabels()
        super(LabelBase, self).__init__(api, args, kwargs)


@ns.route('/')
class Labels(LabelBase):

    # @api.marshal_list_with(job_schema)
    def get(self):
        return db_response_to_json(self.model.get_by_fields())

    @api.response(201, "Added jenkins label")
    @api.expect(label_schema)
    def post(self):
        data = request.json
        rc = self.model.insert(data)
        return None, rc and 201 or 200


@ns.route('/<string:name>')
@api.response(404, 'Site not found.')
class Label(LabelBase):
    @api.response(204, 'Label successfully deleted.')
    def delete(self, name):
        rc = self.model.remove_by_name(name)
        return None, rc and 204 or 404