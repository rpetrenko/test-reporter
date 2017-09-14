# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import logging

from flask import request
from flask_restplus import Resource
from server.api.jenkins.serializers import site_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsSites

log = logging.getLogger(__name__)

ns = api.namespace('jenkins/sites', description='Jenkins sites')


class SiteBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsSites()
        super(SiteBase, self).__init__(api, args, kwargs)


@ns.route('/')
class Sites(SiteBase):

    @api.marshal_list_with(site_schema)
    def get(self):
        log.info("getting sites")
        return db_response_to_json(self.model.get())

    @api.response(201, "Added jenkins site.")
    @api.expect(site_schema)
    def post(self):
        data = request.json
        rc = self.model.insert(data)
        return None, rc and 201 or 200


@ns.route('/<string:name>')
@api.response(404, 'Site not found.')
class Site(SiteBase):

    def get(self, name):
        x = self.model.get(name=name)
        return db_response_to_json(x), x and 200 or 404

    @api.expect(site_schema)
    @api.response(204, 'Site successfully updated.')
    def put(self, name):
        data = request.json
        rc = self.model.update(name, data)
        return None, rc and 204 or 404

    @api.response(204, 'Site successfully deleted.')
    def delete(self, name):
        rc = self.model.remove(name=name)
        return None, rc and 204 or 404


@ns.route('/<string:name>/info')
@api.response(404, 'Site not found.')
class SiteInfo(SiteBase):
    def get(self, name):
        return self.model.get_site_data(name)

