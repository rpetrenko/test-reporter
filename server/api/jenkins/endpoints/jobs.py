# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

from flask import request
from flask_restplus import Resource

from server.api.jenkins.parsers import get_jobs_args
from server.api.jenkins.serializers import job_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsJobs, JenkinsSites


ns = api.namespace('jenkins/jobs', description='Jenkins jobs')


class JobBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsJobs()
        self.sites = JenkinsSites()
        super(JobBase, self).__init__(api, args, kwargs)

    def url_to_name(self, uri):
        uri = uri.rstrip('/')
        parts = uri.split('/job/')
        site = self.sites.get(url=parts[0])
        site = site[0]
        assert site, 'site was not found'
        site_name = site['name']
        parts = [site_name] + parts[1:]
        return ":".join(parts)


@ns.route('/')
class Jobs(JobBase):

    @api.marshal_list_with(job_schema)
    def get(self):
        args = get_jobs_args.parse_args(request)
        label = args.get('label')
        return db_response_to_json(self.model.get_jobs_by_label(label=label))

    @api.response(201, "Added jenkins job.")
    @api.expect(job_schema)
    def post(self):
        data = request.json
        data['name'] = self.url_to_name(data['url'])
        rc = self.model.insert(data)
        return None, rc and 201 or 200


@ns.route('/<string:name>')
@api.response(404, 'Job not found.')
class Job(JobBase):

    def get(self, name):
        x = self.model.get(name=name)
        return db_response_to_json(x), x and 200 or 404

    @api.expect(job_schema)
    @api.response(204, 'Job successfully updated.')
    def put(self, name):
        data = request.json
        rc = self.model.update(name, data)
        return None, rc and 204 or 404

    @api.response(204, 'Job successfully deleted.')
    def delete(self, name):
        rc = self.model.remove(name=name)
        return None, rc and 204 or 404


@ns.route('/<string:name>/info')
@api.response(404, 'Job not found.')
class JobInfo(JobBase):
    def get(self, name):
        return self.model.get_data(self.sites, name)


@ns.route('/<string:name>/builds')
@api.response(404, 'Job not found.')
class JobBuildNumbers(JobBase):
    def get(self, name):
        return self.model.get_builds(self.sites, name)


@ns.route('/labels')
@api.response(404, 'Labels not found.')
class JobLabels(JobBase):
    def get(self):
        x = self.model.get_jobs_labels()
        return db_response_to_json(x), x and 200 or 404


@ns.route('/fetch_data')
@api.response(404, 'Can\'t update data on jobs.')
class JobUpdateData(JobBase):
    def get(self):
        x = self.model.fetch_data_all(self.sites)
        return db_response_to_json(x)

