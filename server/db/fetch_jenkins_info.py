import re
from pymongo import MongoClient
import requests
import json
from server.settings import *
import argparse
import os.path
import urllib3
urllib3.disable_warnings()


def get_label_for_build(labels, build_name):
    """
    get matching label for the build name
    :param labels: 
    :param build: 
    :return: label to apply
    """
    for label in labels:
        patterns = label['build_name_patterns']
        for pattern in patterns:
            m = re.search(str(pattern), build_name)
            if m:
                return label
    return None


def drop_db(client, name):
    print("DROP", name)
    client.drop_database(name)


def populate_db(db, fname):
    """
    Populate DB from file
    :param db: 
    :return: 
    """
    print("Populating DB with sites and jobs from file {}".format(fname))
    assert os.path.isfile(fname), "data file is not found"
    data = eval(open(fname, 'r').read())

    sites = data['sites']
    for site in sites:
        if db.jenkins_sites.find_one({"name": site['name']}):
            continue
        else:
            rec_id = db.jenkins_sites.insert_one(site).inserted_id

    jobs = data['jobs']
    for job in jobs:
        if db.jenkins_jobs.find_one({"name": job['name']}):
            continue
        else:
            rec_id = db.jenkins_jobs.insert_one(job).inserted_id

    labels = data['labels']
    for label in labels:
        if db.jenkins_labels.find_one({"name": label['name']}):
            continue
        else:
            rec_id = db.jenkins_labels.insert_one(label).inserted_id
    print("Done")


class JenkinsFetcher(object):
    def __init__(self, database, api_url):
        self.db = database
        self.api_url = api_url

    def fetch_sites(self):
        sites = self.db.jenkins_sites.find()
        for site in sites:
            print("FS: SITE", site)
            uri = "{}/sites/{}/info".format(self.api_url, site['name'])
            resp = requests.get(uri)
            assert resp.ok, "jenkins site is not reachable {}".format(uri)

    def fetch_builds(self, build_limit=None):
        print("Getting jenkins builds")
        jobs = self.db.jenkins_jobs.find()

        # get builds for each job
        build_names = list()
        for job in jobs:
            print("FB JOB:", job)
            uri = "{}/jobs/{}/builds".format(self.api_url, job['name'])
            resp = requests.get(uri)
            builds = json.loads(resp.text)
            if build_limit:
                builds = builds[:int(build_limit)]
            for build in builds:
                bld_url = job['url'].rstrip('/')
                bld_url = "{}/{}".format(bld_url, build)
                # print("BLD_URL:", bld_url)
                uri = "{}/builds/".format(self.api_url)
                data = {
                    "url": bld_url
                }
                resp = requests.post(uri, json=data)
                assert resp.ok, "error getting build info from jenkins"
                name = json.loads(resp.text)['name']
                build_names.append(name)

        # fetch build info
        for build_name in build_names:
            build = self.db.jenkins_builds.find_one({"name": build_name})
            print("FB BUILD", build)
            uri = "{}/builds/{}/info".format(self.api_url, build['name'])
            resp = requests.get(uri)
            assert resp.ok, "can't fetch build data"

    def apply_labels_to_builds(self):
        # fetch build labels
        uri = "{}/labels".format(self.api_url)
        resp = requests.get(uri)
        labels = json.loads(resp.text)
        builds = self.db.jenkins_builds.find()
        for build in builds:
            if build.get('label'):
                continue
            label = get_label_for_build(labels, build['name'])
            if label:
                parser = eval(label['parser'])
                print("APPLY LABEL", label['name'], "BUILD", build['name'])
                label_data = None
                if "BUILD_INFO_API" == label['url']:
                    uri = "{}/builds/{}/info".format(self.api_url, build['name'])
                    resp = requests.get(uri)
                    if resp.ok:
                        label_data = json.loads(resp.text)
                elif "BUILD_ARTIFACT_API" in label['url']:
                    artifact_pattern = label['artifact_pattern']
                    uri = "{}/builds/{}/artifacts?search=".format(self.api_url, build['name'])
                    uri = "{}{}".format(uri, artifact_pattern)
                    print("ARTIFACT URL", uri)
                    resp = requests.get(uri)
                    if resp.ok:
                        data_ids = json.loads(resp.text)
                        if data_ids:
                            uri = "{}/data/{}".format(self.api_url, data_ids[0])
                            resp = requests.get(uri)
                            f_content = json.loads(resp.text)['data']
                            label_data = f_content['content']

                            print(f_content)
                build = self.db.jenkins_builds.find_one({"name": build['name']})
                if label_data:
                    l = parser(label_data)
                    print("Extracted label", l)
                    build[u'label'] = l
                    print("UPDATING", build['name'])
                    self.db.jenkins_builds.save(build)
            pass

    def fetch_test_results(self):
        print("Getting jenkins test results")
        builds = self.db.jenkins_builds.find()
        for build in builds:
            print("FT BUILD:", build)
            test_url = build['url'].rstrip('/')
            test_url = "{}/testReport".format(test_url)
            uri = "{}/test_reports/".format(self.api_url)
            data = {
                "url": test_url
            }
            resp = requests.post(uri, json=data)
            assert resp.ok, "can't fetch test report metadata"

        reports = self.db.jenkins_test_reports.find()
        for report in reports:
            print("FT REPORT", report)
            uri = "{}/test_reports/{}/info".format(self.api_url, report['name'])
            print("GET {}".format(uri))
            resp = requests.get(uri)
            assert resp.ok, "can't fetch test report"


def main():
    client = MongoClient()
    if args.drop_db:
        drop_db(client, MONGO_DBNAME)
        return

    db = client.reporting
    # populate with sites and jobs from .data file
    populate_db(db, args.data_file)

    # fetch jenkins info and store in DB
    server_url = "http://{}:{}/api/jenkins".format(args.host, args.port)
    jf = JenkinsFetcher(db, server_url)
    jf.fetch_sites()
    if args.get_builds:
        jf.fetch_builds(build_limit=args.build_limit)
        jf.apply_labels_to_builds()
    if args.get_tests:
        jf.fetch_test_results()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host",
                        help="report server host",
                        default="localhost")
    parser.add_argument("-P", "--port",
                        help="report server port",
                        default="5001")
    parser.add_argument("-F", "--data_file",
                        help="data file to pre populate DB",
                        default="server/db/.data")
    parser.add_argument("-L", "--build_limit",
                        default=None,
                        help="limit the number of builds to fetch from jenkins for each job")
    parser.add_argument('-D', '--drop_db',
                        required=False,
                        default=False,
                        action='store_const',
                        const='True',
                        help='Drop database'
                        )
    parser.add_argument('-B', '--get_builds',
                        required=False,
                        default=False,
                        action='store_const',
                        const='True',
                        help='Get jenkins builds'
                        )
    parser.add_argument('-T', '--get_tests',
                        required=False,
                        default=False,
                        action='store_const',
                        const='True',
                        help='Get jenkins test reports'
                        )
    args = parser.parse_args()
    main()
