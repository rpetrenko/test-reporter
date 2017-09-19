# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import logging
from flask import request
from flask_restplus import Resource
from server.api.jenkins.parsers import get_args, get_data_args, get_cases_args
from server.api.jenkins.serializers import test_report_schema
from server.api.common import api, db_response_to_json
from server.db.models import JenkinsTestReports, JenkinsSites

ns = api.namespace('jenkins/test_reports', description='Jenkins test reports')
log = logging.getLogger(__name__)


class TestReportBase(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.model = JenkinsTestReports()
        self.sites = JenkinsSites()
        super(TestReportBase, self).__init__(api, args, kwargs)

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
class TestReports(TestReportBase):

    @api.expect(get_args)
    @api.marshal_list_with(test_report_schema)
    def get(self):
        args = get_args.parse_args(request)
        data = args.get('data_only', None)
        last = args.get('last', None)
        data_fields = args.get('data_fields', None)
        names = args.get('names', None)
        resp = self.model.get_reports(data=data,
                                      last=last,
                                      data_fields=data_fields,
                                      names=names)
        log.info("Got {} records for test reports".format(len(resp)))
        return resp

    @api.response(201, "Added jenkins build.")
    @api.expect(test_report_schema)
    def post(self):
        """
        data structure:
        {
            url: <jenkins_url/build_number/testReport>,
            data: null,
            name: site:url_job_path:build_number:testReport
        }
        this just creates DB record for the build, the test results
        are populated by /<string:name>/info GET request
        reference to data is None here
        :return: 
        """
        data = request.json
        data['name'] = self.url_to_name(data['url'])
        names = data['name'].split(':')
        data['job'] = ":".join(names[:-2])
        data['build'] = names[-2]
        rc = self.model.insert(data)
        return None, rc and 201 or 200


@ns.route('/data')
class TestReportsData(TestReportBase):

    @api.expect(get_data_args)
    # @api.marshal_list_with(test_report_schema)
    def get(self):
        args = get_data_args.parse_args(request)
        data_fields = args.get('data_fields', None)
        resp = self.model.get(data_fields=data_fields)
        log.info("Got {} records for test reports".format(len(resp)))
        return db_response_to_json(resp)


@ns.route('/<string:name>')
@api.response(404, 'Report not found.')
class TestReport(TestReportBase):

    def get(self, name):
        x = self.model.get(name=name)
        return db_response_to_json(x), x and 200 or 404

    @api.expect(test_report_schema)
    @api.response(204, 'Report successfully updated.')
    def put(self, name):
        data = request.json
        rc = self.model.update(name, data)
        return None, rc and 204 or 404

    @api.response(204, 'Report successfully deleted.')
    def delete(self, name):
        rc = self.model.remove(name=name)
        return None, rc and 204 or 404


@ns.route('/<string:name>/info')
@api.response(404, 'Report not found.')
class TestReportInfo(TestReportBase):
    """
    Test results are populated here
    """
    def get(self, name):
        data, rc = self.model.get_data(self.sites, name)
        return data, rc


@ns.route('/<string:name>/suites')
@api.response(404, 'Report suites not found.')
class TestReportSuites(TestReportBase):
    """
    Test results are populated here
    """
    def get(self, name):
        data, rc = self.model.get_suites(name)
        return data, rc


@ns.route('/<string:name>/cases')
@api.response(404, 'Report cases not found.')
class TestReportCases(TestReportBase):
    """
    Test results are populated here
    """
    @api.expect(get_cases_args)
    def get(self, name):
        args = get_cases_args.parse_args(request)
        cases_fields = args.get('cases_fields', None)
        data, rc = self.model.get_cases(name, cases_fields=cases_fields)
        return data, rc


@ns.route('/suites/<string:suite_id>')
@api.response(404, 'Report suite not found.')
class TestReportSuite(TestReportBase):
    """
    Get test suite by it's id
    """
    def get(self, suite_id):
        data, rc = self.model.get_suites_by_id(suite_id)
        return data, rc

@ns.route('/cases/<string:case_id>')
@api.response(404, 'Report case not found.')
class TestReportCase(TestReportBase):
    """
    Get test case by it's id
    """
    def get(self, case_id):
        data, rc = self.model.get_cases_by_id(case_id)
        return data, rc