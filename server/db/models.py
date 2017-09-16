# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import requests
import json
from bson.objectid import ObjectId
import logging
import re

from server.db import db
from server.api.common import jenkins_response_to_json, \
    create_jenkins_uri, \
    insert_creds_to_jenkins_url, \
    db_response_to_json
import urllib3
urllib3.disable_warnings()

log = logging.getLogger(__name__)


class DbDocument(object):
    collection = None

    def get_doc(self, doc_id=None):
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

    def get_by_fields(self, **kwargs):
        query = dict()
        if kwargs:
            name = kwargs.get('name')
            url = kwargs.get('url')
            label = kwargs.get('label')
            if name:
                query["name"] = name
            elif url:
                query["url"] = url
            if label:
                query["label"] = label
        if query:
            docs = self.collection.find(query)
        else:
            docs = self.collection.find()
        docs = list(docs)
        return docs

    def get_count(self):
        return self.collection.count()

    def insert(self, data, allow_duplicates=None):
        """
        
        :param data: 
        :param allow_duplicates: 
        :return: 
        """
        if self.collection.count({'name': data['name']}) and not allow_duplicates:
            return False
        else:
            rec_id = self.collection.insert_one(data).inserted_id
            assert rec_id, "entry was not created"
            return rec_id

    def remove_by_name(self, name):
        resp = self.collection.remove({"name": name})
        assert resp['n'] > 0, "can't delete document {}".format(name)
        return True


class JenkinsData(DbDocument):
    def __init__(self):
        self.collection = db.db.jenkins_data


class JenkinsLabels(DbDocument):
    def __init__(self):
        self.collection = db.db.jenkins_labels


class JenkinsBase(DbDocument):
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

    def populate_data(self, documents, data_fields, ts_from=None, ts_to=None):
        r = list()
        for doc in documents:
            # builds not completed don't have 'data' field reference
            if doc.get('data'):
                x = self.get_data_record(doc['data'])
                if x.get('data') != 'null':
                    x = x['data']
                    x = json.loads(x)
                    d = dict()
                    if data_fields == "*":
                        d = x
                    else:
                        fields = data_fields.split(',')
                        for f in fields:
                            if f in x.keys():
                                d[f] = x[f]
                    doc['data'] = d
                    append_this = True
                    if ts_from and ts_from > x['timestamp']:
                        append_this = False
                    if ts_to and ts_to < x['timestamp']:
                        append_this = False
                    if append_this:
                        r.append(doc)
        return r

    def get(self, name=None, url=None, data=None, data_fields=None, ts_from=None, ts_to=None):
        res = self.get_by_fields(name=name, url=url)
        if data:
            res = [r for r in res if self.has_data(r)]
        if data_fields:
            # populate and filter data
            res = self.populate_data(res, data_fields, ts_from=ts_from, ts_to=ts_to)
        return res

    def remove(self, name):
        return self.remove_by_name(name)

    def update(self, name, data):
        document = self.get(name=name)
        document = document[0]
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

    def get_data_records(self, data_ids):
        res = list()
        for data_id in data_ids:
            r = self.get_data_record(data_id)
            res.append(json.loads(r['data']))
        return res

    def _get_data(self, doc):
        if not doc:
            return None, 404
        x = doc[0]
        if x.get('data', None):
            # fetch data locally
            data_id = x['data']
            data = self.get_data_record(data_id)
            return json.loads(data['data']), 200
        else:
            return None, 200

    def get_data(self, sites, name):
        doc = self.get(name=name)
        data, rc = self._get_data(doc)
        if not data and rc == 200:
            # fetch data from jenkins
            x = doc[0]
            site_name = x['name'].split(':')[0]
            site = sites.get(name=site_name)
            site = site[0]
            data, rc = self._get_jenkins_url(site, x['url'])
            if data:
                self.add_data_to_doc(x, data)
        return data, rc

    def _get_jenkins_url(self, site, uri):
        uri = create_jenkins_uri(site['username'], site['api_key'], uri)
        log.info("GET: {}".format(uri))
        resp = requests.get(uri, verify=False)
        data = None
        if resp.ok:
            data = jenkins_response_to_json(resp.text)
            if data.get('building'):
                log.info("SKIP builds that are not complete")
        else:
            log.error(resp.text)
        return data, resp.status_code


class JenkinsSuites(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_suites
        super(JenkinsSuites, self).__init__()


class JenkinsCases(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_cases
        super(JenkinsCases, self).__init__()


class JenkinsSites(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_sites
        super(JenkinsSites, self).__init__()

    def get_site_data(self, name):
        doc = self.get(name=name)
        data, rc = self._get_data(doc)
        if not data and rc == 200:
            # fetch data from jenkins
            x = doc[0]
            site = self.get(name=name)
            site = site[0]
            data, rc = self._get_jenkins_url(site, x['url'])
            if data:
                self.add_data_to_doc(x, data)
        return data, rc


class JenkinsJobs(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_jobs
        super(JenkinsJobs, self).__init__()

    def get_builds(self, sites, name):
        doc = self.get(name=name)
        data, rc = self._get_data(doc)
        if not data and rc == 200:
            x = doc[0]
            site_name = x['name'].split(':')[0]
            site = sites.get(name=site_name)
            site = site[0]
            data, rc = self._get_jenkins_url(site, x['url'])
            if data:
                self.add_data_to_doc(x, data)

        if not data:
            builds = []
        else:
            data_builds = data.get('builds')
            if data_builds:
                builds = [x['number'] for x in data_builds if x.get('number')]
            else:
                builds = []
        return builds, 200

    def get_jobs_by_label(self, label=None):
        res = self.get_by_fields(label=label)
        return res


class JenkinsBuilds(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_builds
        super(JenkinsBuilds, self).__init__()

    def filter_artifacts(self, artifacts, search):
        """
        
        :param search: list of file search patterns 
        :return: 
        """
        if search:
            search = eval(search)
            arts = list()
            for artifact in artifacts:
                for s in search:
                    fname = artifact['relativePath']
                    if re.search(str(s), fname):
                        arts.append(artifact)
                        break
        else:
            arts = artifacts
        return arts

    def get_artifacts(self, sites, name, artifacts):
        if not artifacts:
            return []
        build = self.get(name=name)
        build = build[0]
        artifact_ids = list()
        if build.get('artifacts'):
            artifact_ids = build['artifacts']
            existing_artifacts = self.get_data_records(artifact_ids)
            existing_artifacts_paths = [x['name'] for x in existing_artifacts]
            artifacts = [x for x in artifacts if x['relativePath'] not in existing_artifacts_paths]
        if artifacts:
            num_artifacts = len(artifacts)
            log.info("Fetching {} artifacts from build {}".format(num_artifacts, build['name']))
            site_name = build['name'].split(':')[0]
            site = sites.get(name=site_name)
            site = site[0]
            rec_ids = list()
            for art in artifacts:
                art_uri = "{}/artifact/{}".format(build['url'], art['relativePath'])
                uri = insert_creds_to_jenkins_url(site['username'], site['api_key'], art_uri)
                resp = requests.get(uri, verify=False)
                if resp.ok:
                    d = json.loads(resp.text)
                    data = {
                        "name": art['relativePath'],
                        "content": d
                    }
                    rec_id = self.insert_data(data)
                    rec_ids.append(str(rec_id))
            build['artifacts'] = artifact_ids + rec_ids
            self.update(build['name'], build)
            build = self.get(name=name)
            build = build[0]
        return build['artifacts']


class JenkinsTestReports(JenkinsBase):
    def __init__(self):
        self.collection = db.db.jenkins_test_reports
        self.suites = JenkinsSuites()
        self.cases = JenkinsCases()
        super(JenkinsTestReports, self).__init__()

    def get_tests_from_builds(self, builds_response, test_data_fields=None):
        res = list()
        for build in builds_response:
            build_name = build['name']
            test_report_name = "{}:testReport".format(build_name)
            if not test_data_fields:
                test_data_fields = "*"
            resp = self.get(name=test_report_name, data_fields=test_data_fields)
            if resp:
                resp = resp[0]
                d = {
                    "name": resp["name"],
                    "url": resp["url"],
                    "build_data": build["data"],
                    "test_data": resp["data"],
                    "label": build.get("label")
                }
                res.append(d)
        return res

    def insert_cases(self, cases):
        case_ids = list()
        for case in cases:
            # import bson
            # print(len(bson.BSON.encode(suite)))
            case_id = self.cases.insert(case)
            if case_id:
                case_ids.append(case_id)
        return case_ids

    def insert_suites(self, suites):
        suite_ids = list()
        for suite in suites:
            if suite.get('cases'):
                case_ids = self.insert_cases(suite['cases'])
                suite['cases'] = case_ids
            suite_id = self.suites.insert(suite, allow_duplicates=True)
            if suite_id:
                suite_ids.append(str(suite_id))
        return suite_ids

    def get_suites(self, name):
        doc = self.get(name=name, data_fields="suites")
        x = doc[0]
        suite_ids = x['data'].get('suites', list())
        res = list()
        for suite_id in suite_ids:
            s, _ = self.get_suites_by_id(suite_id)
            res.append(s)
        return res, 200

    def get_suites_by_id(self, suite_id):
        s = self.suites.get_doc(doc_id=suite_id)
        s['_id'] = str(s['_id'])
        if s.get('cases'):
            s['cases'] = [str(case_id) for case_id in s['cases']]
        return s, 200

    def get_cases_by_id(self, case_id):
        s = self.cases.get_doc(doc_id=case_id)
        s['_id'] = str(s['_id'])
        return s, 200

    def get_data(self, sites, name):
        """
        Overrides base class method since we want to store suites data separately
        :param sites: 
        :param name: 
        :return: 
        """
        doc = self.get(name=name)
        data, rc = self._get_data(doc)
        if not data and rc == 200:
            # fetch data from jenkins
            x = doc[0]
            site_name = x['name'].split(':')[0]
            site = sites.get(name=site_name)
            site = site[0]
            data, rc = self._get_jenkins_url(site, x['url'])
            if data and data.get('suites'):
                # store suites in separate collection
                suites = data['suites']
                suite_ids = self.insert_suites(suites)
                data['suites'] = suite_ids
                self.add_data_to_doc(x, data)
        return data, rc

    def get_reports(self, data=None, last=None, data_fields=None):
        res = self.get_by_fields()
        if data:
            res = [r for r in res if self.has_data(r)]
        elif data is None:
            pass
        else:
            res = [r for r in res if not self.has_data(r)]
        if last:
            jobs = set([r['job'] for r in res])
            x = list()
            for job in jobs:
                r_job = [r for r in res if r['job'] == job]
                builds = [r['build'] for r in r_job]
                builds = sorted(builds, reverse=True)
                builds = builds if len(builds) <= last else builds[:last]
                x = x + [r for r in r_job if r['job'] == job and r['build'] in builds]
            res = x
        if data and data_fields:
            # populate and filter data
            res = self.populate_data(res, data_fields)
        return res

