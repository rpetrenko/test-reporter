# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

from flask_restplus import fields
from server.api.common import api


site_schema = api.model('Jenkins sites', {
    'name': fields.String(required=True, description='Jenkins name'),
    'url': fields.String(required=True, description="Jenkins URL"),
    # 'username': fields.String(required=True, description="Jenkins user"),
    # 'api_key': fields.String(required=True, description="Jenkins API key"),
    'data': fields.String(required=False, description='jenkins json data')
})

job_schema = api.model('Jenkins jobs', {
    'url': fields.String(required=True, description="job url"),
    'name': fields.String(required=False, description='job name'),
    'data': fields.String(required=False, description='jenkins json data')
})

build_schema = api.model('Jenkins builds', {
    'url': fields.String(required=True, description='build url'),
    'name': fields.String(required=False, description="build name"),
    'data': fields.String(required=False, description='jenkins json data'),
    'label': fields.String(required=False, description='build label'),
    'artifacts': fields.String(required=False, description='build artifacts')
})


test_report_schema = api.model('Jenkins test reports', {
    'url': fields.String(required=True, description='test report url'),
    'name': fields.String(required=False, description="test report name"),
    'job': fields.String(required=False, description='job name'),
    'build': fields.String(required=False, description='build number'),
    'data': fields.String(required=False, description='jenkins json data')
})

label_schema = api.model('Jenkins labels', {
    'url': fields.String(required=True, description="build's artifact url"),
    'name': fields.String(required=False, description="label name"),
    'parsing': fields.String(required=False,
                             description="response parsing function, e.g: lambda x: x['response']")
})

