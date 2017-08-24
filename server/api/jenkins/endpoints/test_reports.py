import logging
from flask import request
from flask_restplus import Resource
from server.api.jenkins.parsers import get_args, get_data_args
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
        data = args.get('data_only', False)
        resp = self.model.get(data=data)
        log.info("Got {} records for test reports".format(len(resp)))
        return resp

    @api.response(201, "Added jenkins build.")
    @api.expect(test_report_schema)
    def post(self):
        data = request.json
        data['name'] = self.url_to_name(data['url'])
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
    def get(self, name):
        data, rc = self.model.get_data(self.sites, name)
        if rc == 404:
            # handle test report when there is no data
            x = self.model.get(name=name)
            x = x[0]
            self.model.add_data_to_doc(x, data)
            rc = 200
        return data, rc

