from pymongo import MongoClient
import requests
import json
from server.settings import *
import argparse
import os.path


def drop_db(client, name):
    print("DROP", name)
    client.drop_database(name)


def populate_db(db, fname):
    """
    Populate DB from file
    :param db: 
    :return: 
    """
    print("Populating DB with sites and jobs from .data file")
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
            rec_ic = db.jenkins_jobs.insert_one(job).inserted_id
    print("Done")


class JenkinsFetcher(object):
    def __init__(self, database, api_url):
        self.db = database
        self.api_url = api_url

    def fetch_builds(self):
        print("Getting jenkins builds")
        jobs = self.db.jenkins_jobs.find()
        for job in jobs:
            print("FB JOB:", job)
            uri = "{}/jobs/{}/builds".format(self.api_url, job['name'])
            resp = requests.get(uri)
            builds = json.loads(resp.text)
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

        builds = self.db.jenkins_builds.find()
        for build in builds:
            print("FB BUILD", build)
            uri = "{}/builds/{}/info".format(self.api_url, build['name'])
            resp = requests.get(uri)
            assert resp.ok, "can't fetch build data"

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
            resp = requests.get(uri)
            pass


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
    if args.get_builds:
        jf.fetch_builds()
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
