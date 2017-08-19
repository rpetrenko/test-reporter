from flask_restplus import Resource
from server.api.common import api
from server.db.models import JenkinsSites, JenkinsJobs, JenkinsBuilds, JenkinsTestReports

ns = api.namespace('jenkins/stats', description='Reporting server stats')


class StatsBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.sites = JenkinsSites()
        self.jobs = JenkinsJobs()
        self.builds = JenkinsBuilds()
        self.test_reports = JenkinsTestReports()
        super(StatsBase, self).__init__(api, args, kwargs)


@ns.route('/')
class Stats(StatsBase):
    def get(self):
        data = {
            'sites': self.sites.get_count(),
            'jobs': self.jobs.get_count(),
            'builds': self.builds.get_count(),
            'test_reports': self.test_reports.get_count(),
            'data': self.sites.data_collection.count()
        }
        return data, 200
