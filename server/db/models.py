import requests
import json
from bson.objectid import ObjectId
import logging

from server.db import db
from server.api.common import jenkins_response_to_json, create_jenkins_uri, db_response_to_json

log = logging.getLogger(__name__)


class JenkinsBase(object):
    collection = None
    data_collection = None

    def __init__(self):
        self.data_collection = db.db.jenkins_data

    def has_data(self, document):
        data_id = document.get('data')
        if data_id:
            resp = self.get_data_record(data_id)
            if resp['data'] != 'null':
                return True
        return False

    def get(self, name=None, url=None, data=None):
        if name:
            res = self.collection.find_one({"name": name})
        elif url:
            res = self.collection.find_one({"url": url})
        else:
            docs = self.collection.find()
            docs = list(docs)
            res = docs
        if data:
            if isinstance(res, list):
                return [r for r in res if self.has_data(r)]
            else:
                return res if self.has_data(res) else ''
        else:
            return res

    def insert(self, data):
        if self.collection.count({'name': data['name']}) == 0:
            rec_id = self.collection.insert_one(data).inserted_id
            assert rec_id, "entry was not created"
            return True
        else:
            return False

    def remove(self, name):
        resp = self.collection.remove({"name": name})
        assert resp['n'] > 0, "can't delete document {}".format(name)
        return True

    def update(self, name, data):
        document = self.get(name=name)
        if not document:
            return False
        for k, v in data.items():
            document[k] = v
        self.collection.save(document)
        return True

    def insert_data(self, data):
        db_resp = self.data_collection.insert_one({"data": json.dumps(data)})
        rec_id = db_resp.inserted_id
        return rec_id

    def add_data_to_doc(self, document, data):
        rec_id = self.insert_data(data)
        document['data'] = str(rec_id)
        self.update(document['name'], document)

    def get_data_record(self, data_id):
        return self.data_collection.find_one({"_id": ObjectId(data_id)})

    def get_data(self, sites, name):
        x = self.get(name=name)
        if not x:
            return None, 404

        if x.get('data', None):
            # fetch data locally
            data_id = x['data']
            data = self.get_data_record(data_id)
            return json.loads(data['data']), 200

        if len(name.split(':')) == 1:  # this is sites itself
            site = self.get(name=name)
        else:
            site_name = x['name'].split(':')[0]
            site = sites.get(name=site_name)
        uri = create_jenkins_uri(site['username'], site['api_key'], x['url'])
        log.info("GET: {}".format(uri))
        resp = requests.get(uri, verify=False)
        data = None
        if resp.ok:
            data = jenkins_response_to_json(resp.text)
            if data.get('building'):
                log.info("SKIP builds that are not complete")
            else:
                self.add_data_to_doc(x, data)
        else:
            log.error(resp.text)
        return data, resp.status_code

    def get_count(self):
        return self.collection.count()


class JenkinsSites(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_sites
        super(JenkinsSites, self).__init__()


class JenkinsJobs(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_jobs
        super(JenkinsJobs, self).__init__()

    def get_builds(self, sites, name):
        data, rc = self.get_data(sites, name)
        builds = [x['number'] for x in data['builds']]
        return builds, 200


class JenkinsBuilds(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_builds
        super(JenkinsBuilds, self).__init__()


class JenkinsTestReports(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_test_reports
        super(JenkinsTestReports, self).__init__()


class JenkinsData(object):
    def __init__(self):
        self.collection = db.db.jenkins_data

    def get(self, doc_id=None):
        """
        :param doc_id: document id
        :return: if not specified, returned list of ids, otherwise record with data
        """
        if doc_id:
            resp = self.collection.find_one({"_id": ObjectId(doc_id)})
        else:
            resp = self.collection.find({}, {"_id": 1})
            resp = list(resp)
        return resp



