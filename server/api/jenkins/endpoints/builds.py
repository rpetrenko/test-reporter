
from flask import request
from flask_restplus import Resource
from server.api.jenkins.serializers import build_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsBuilds, JenkinsSites

ns = api.namespace('jenkins/builds', description='Jenkins builds')


class BuildBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsBuilds()
        self.sites = JenkinsSites()
        super(BuildBase, self).__init__(api, args, kwargs)

    def url_to_name(self, uri):
        uri = uri.rstrip('/')
        parts = uri.split('/job/')
        site = self.sites.get(url=parts[0])
        assert site, 'site was not found'
        site_name = site['name']
        parts = [site_name] + parts[1:-1] + parts[-1].split('/')
        return ":".join(parts)


@ns.route('/')
class Builds(BuildBase):

    @api.marshal_list_with(build_schema)
    def get(self):
        # log.info("getting sites")
        return db_response_to_json(self.model.get())

    @api.response(201, "Added jenkins build.")
    @api.expect(build_schema)
    def post(self):
        data = request.json
        data['name'] = self.url_to_name(data['url'])
        rc = self.model.insert(data)
        return None, rc and 201 or 200


@ns.route('/<string:name>')
@api.response(404, 'Build not found.')
class Build(BuildBase):

    def get(self, name):
        x = self.model.get(name=name)
        return db_response_to_json(x), x and 200 or 404

    @api.expect(build_schema)
    @api.response(204, 'Build successfully updated.')
    def put(self, name):
        data = request.json
        rc = self.model.update(name, data)
        return None, rc and 204 or 404

    @api.response(204, 'Build successfully deleted.')
    def delete(self, name):
        rc = self.model.remove(name=name)
        return None, rc and 204 or 404


@ns.route('/<string:name>/info')
@api.response(404, 'Job not found.')
class BuildInfo(BuildBase):
    def get(self, name):
        return self.model.get_data(self.sites, name)
