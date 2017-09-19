# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import logging
from flask import request
from flask_restplus import Resource
import json

from server.api.jenkins.parsers import get_data_args, get_artifacts_args, get_build_args
from server.api.jenkins.serializers import build_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsBuilds, JenkinsSites, JenkinsJobs

ns = api.namespace('jenkins/builds', description='Jenkins builds')
log = logging.getLogger(__name__)


class BuildBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsBuilds()
        self.sites = JenkinsSites()
        self.jobs = JenkinsJobs()
        super(BuildBase, self).__init__(api, args, kwargs)

    def url_to_name(self, uri):
        uri = uri.rstrip('/')
        parts = uri.split('/job/')
        site = self.sites.get(url=parts[0])
        site = site[0]
        assert site, 'site was not found'
        site_name = site['name']
        parts = [site_name] + parts[1:-1] + parts[-1].split('/')
        return ":".join(parts)


@ns.route('/')
class Builds(BuildBase):

    @api.expect(get_build_args)
    @api.marshal_list_with(build_schema)
    def get(self):
        args = get_build_args.parse_args(request)
        job_label = args.get('job_label', None)
        if job_label:
            jobs = self.jobs.get_jobs_by_label(job_label)
            resp = self.model.get_builds(jobs=jobs)
        else:
            resp = self.model.get()
        return db_response_to_json(resp)

    @api.response(201, "Added jenkins build.")
    @api.expect(build_schema)
    def post(self):
        data = request.json
        data['name'] = self.url_to_name(data['url'])
        rc = self.model.insert(data)
        return {"name": data['name']}, rc and 201 or 200


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
@api.response(404, 'Build not found.')
class BuildInfo(BuildBase):
    def get(self, name):
        return self.model.get_data(self.sites, name)


@ns.route('/<string:name>/artifacts')
@api.response(404, 'Build not found.')
class BuildArtifacts(BuildBase):
    @api.expect(get_artifacts_args)
    def get(self, name):
        args = get_artifacts_args.parse_args(request)
        search = args.get('search', None)
        res, rc = self.model.get_data(self.sites, name)
        if rc == 200 and res.get('artifacts'):
            artifacts = self.model.filter_artifacts(res['artifacts'], search)
            return self.model.get_artifacts(self.sites, name, artifacts)
        else:
            return ''


@ns.route('/data')
class BuildsData(BuildBase):

    @api.expect(get_data_args)
    # @api.marshal_list_with(test_report_schema)
    def get(self):
        args = get_data_args.parse_args(request)
        data_fields = args.get('data_fields', None)
        ts_from = args.get('ts_from', None)
        ts_to = args.get('ts_to', None)
        resp = self.model.get(data_fields=data_fields, ts_from=ts_from, ts_to=ts_to)
        log.info("Got {} records for test reports".format(len(resp)))
        return db_response_to_json(resp)