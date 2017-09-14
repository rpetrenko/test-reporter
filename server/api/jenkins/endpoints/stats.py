# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

"""
This should work only with internal database, no requests to jenkins should be made here
"""
import logging
from flask import request
from flask_restplus import Resource
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsSites, \
    JenkinsJobs, \
    JenkinsBuilds, \
    JenkinsTestReports, \
    JenkinsLabels
from server.api.jenkins.parsers import get_data_args

ns = api.namespace('reporter', description='Reporting server stats')
log = logging.getLogger(__name__)


class ReporterBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.sites = JenkinsSites()
        self.jobs = JenkinsJobs()
        self.builds = JenkinsBuilds()
        self.test_reports = JenkinsTestReports()
        self.labels = JenkinsLabels()
        super(ReporterBase, self).__init__(api, args, kwargs)


@ns.route('/stats')
class Stats(ReporterBase):
    def get(self):
        data = {
            'sites': self.sites.get_count(),
            'jobs': self.jobs.get_count(),
            'builds': self.builds.get_count(),
            'test_reports': self.test_reports.get_count(),
            'data': self.sites.data_collection.count(),
            'labels': self.labels.get_count(),
            'suites': self.test_reports.suites.get_count()
        }
        return data, 200


@ns.route('/tests')
class Reporter(ReporterBase):
    @api.expect(get_data_args)
    def get(self):
        args = get_data_args.parse_args(request)
        data_fields = args.get('data_fields', None)
        ts_from = args.get('ts_from', None)
        ts_to = args.get('ts_to', None)
        builds_resp = self.builds.get(data_fields=data_fields, ts_from=ts_from, ts_to=ts_to)
        log.info("Got {} records for test reports".format(len(builds_resp)))
        log.info("Getting test results corresponding to builds")
        resp = self.test_reports.get_tests_from_builds(builds_resp,
                                                       test_data_fields=data_fields)
        return db_response_to_json(resp)
