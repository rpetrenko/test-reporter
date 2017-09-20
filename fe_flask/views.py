from datetime import datetime
from flask import render_template
import json
import requests
import pandas as pd
from settings import API_URL

# to avoid truncation
pd.set_option('display.max_colwidth', -1)


def convert_times(date_from, date_to):
    date_from, date_to = str(date_from), str(date_to)
    dt_start = datetime.strptime(date_from, '%Y-%m-%d')
    dt_end = datetime.strptime(date_to, '%Y-%m-%d')
    return dt_start, dt_end


# with open('mapping.json') as data_file:
#     mapping = json.load(data_file)


def get_first_n(label, first_n, sep=None, last_n=None):
    if not sep:
        sep = "."
    x = label.split(sep)
    if last_n:
        x = x[last_n:]
    else:
        x = x[:first_n]
    return sep.join(x)


def _get_data_as_json(uri):
    print("Request to TR-API", uri)
    r = requests.get(uri)
    out = None
    if r.ok:
        out = json.loads(r.text)
    return out


def _get_data_as_dataframe(uri):
    out = _get_data_as_json(uri)
    if out:
        out = pd.DataFrame(out)
    return out


def get_jobs():
    uri = "{}/jobs/".format(API_URL)
    return _get_data_as_dataframe(uri)


def get_builds(job_label):
    data_fields = "timestamp,result"
    uri = "{}/builds/?job_label={}&data_fields={}".format(API_URL, job_label, data_fields)
    df = _get_data_as_dataframe(uri)
    # remove records without labels
    df = df.dropna(subset=['label'])
    df['temp'] = df['name'].apply(lambda x: str({"build": x.split(':')[-1], "job": ":".join(x.split(':')[:-1])}))
    df = pd_spread_to_columns(df, 'temp')
    if data_fields:
        df = pd_spread_to_columns(df, 'data')
        df['date'] = df['timestamp'].apply(
            lambda x: pd.to_datetime(int(x)/1000, unit='s'))
    # print(df.iloc[0, :])
    return df


def create_product_list(df):
    products = list()
    columns = ["short_name", "url_y", "failCount", "passCount", "total"]
    names = df['label'].unique()
    for name in names:
        df_jobs = df[df["label"] == name][columns]
        df_jobs_sum = df_jobs.sum()
        failed = int(df_jobs_sum['failCount'])
        passed = int(df_jobs_sum['passCount'])
        tot = failed + passed
        jobs = df_jobs.to_dict(orient='list')
        p = {"name": name, "jobs": jobs, "failed": failed, "tot": tot}
        products.append(p)
    return products


def pd_spread_to_columns(df, col_name):
    existing_cols = df.columns
    df2 = df[col_name].apply(lambda x: eval(x))
    for k in df2.iloc[0].keys():
        if k in existing_cols:
            new_k = "{}_{}".format(col_name, k)
        else:
            new_k = k
        df[new_k] = df2.apply(lambda x: x[k])
    del df[col_name]
    return df


def pd_embed_url(df, col_name, url_col_name, new_tab=True):
    if new_tab:
        new_tab = "\" target=\"_blank\">"
    else:
        new_tab = "\">"
    df1 = "<a href=\"" + df[url_col_name].astype(str) + new_tab + df[col_name].astype(str) + "</a>"
    df[col_name] = df1
    del df[url_col_name]
    return df


def pd_to_html(df, **kwargs):
    cols = kwargs.get('cols')
    if cols:
        df = df[cols]
        del kwargs['cols']
    df_html = df.to_html(justify="left",
                         index=False,
                         classes="table table-striped table-hover table-condensed",
                         border=0, **kwargs)
    return df_html


def get_test_reports(names=None):
    """
    
    :param names: build names on report server
    :return: 
    """
    fields = "suites,failCount,skipCount,duration,passCount"
    uri = "{}/test_reports/?data_only=1&last=1&data_fields={}".format(API_URL, fields)
    if names:
        names_str = ",".join(names)
        uri = "{}&names={}".format(uri, names_str)
    df = _get_data_as_dataframe(uri)

    test_reports = pd_spread_to_columns(df, 'data')
    test_reports["total"] = test_reports["failCount"] + test_reports["passCount"]
    return test_reports


def get_test_suites(name):
    """
    Example:
    /api/jenkins/test_reports/<test_report_name>/cases?cases_fields=status%2Cname%2Cduration%2CclassName
    :param name: test report name
    :return: 
    """
    options = "status,duration,name,className,age,errorDetails"
    uri = "{}/test_reports/{}/cases?cases_fields={}".format(API_URL, name, options)
    out = _get_data_as_json(uri)
    if not out:
        return None
    cases = list()
    for suite in out:
        for case in suite['cases']:
            case['suite_name'] = suite['name']
            cases.append(case)
    df = pd.DataFrame(cases)
    df['T, s'] = df['duration'].astype(int)
    return df


def home_view():
    df_jobs = get_jobs()

    df_jobs["short_name"] = df_jobs["name"].apply(lambda x: x.split(":")[-1])
    df_test_reports = get_test_reports()
    jobs_with_reports = pd.merge(df_jobs,
                                 df_test_reports,
                                 how="left",
                                 left_on="name",
                                 right_on="job")
    products = create_product_list(jobs_with_reports)
    return render_template('index.html', products=products)


def platform_view(name):
    """
    TODO:
        1. get all jobs for label Maglev
        2. get all builds for given job list
        3. group results by version (label at build level)
    :param name: 
    :return: 
    """
    df_builds = get_builds(job_label=name)

    df_builds['branch'] = df_builds['label'].apply(get_first_n, args=(3,), sep=".")
    df_builds = df_builds.groupby(['branch', 'job']).max().reset_index()

    # now populate with test results
    build_names = df_builds['name'].tolist()
    df_test_reports = get_test_reports(names=build_names)
    df_test_reports['build_name'] = df_test_reports['name'].apply(get_first_n, args=(-1,), sep=":")
    df_builds = pd.merge(df_builds,
                         df_test_reports,
                         how="left",
                         left_on="name",
                         right_on="build_name")
    # df_builds = pd_embed_url(df_builds, 'name_x', 'url_x')
    df_builds['tr_url'] = df_builds.apply(lambda x: "/platform/{}/label/{}/test_report/{}".format(name, x['label'], x['name_y']), axis=1)
    df_builds = pd_embed_url(df_builds, 'name_x', 'tr_url', new_tab=False)
    df_builds = df_builds.sort_values(['label', 'failCount'], ascending=False)

    # print(df_builds.iloc[0, :])

    cols = ["label", "name_x", "failCount", "total", "duration", "date", "result"]
    branches = df_builds['branch'].unique()
    builds_htmls = list()
    for branch in branches:
        df = df_builds[df_builds['branch'] == branch]
        failed = df['failCount'].sum()
        total = df['total'].sum()
        builds_html = pd_to_html(df, escape=False, cols=cols)
        builds_htmls.append(
            {
                "branch": branch,
                "failed": failed,
                "total": total,
                "html": builds_html
            }
        )
    return render_template('platform.html', name=name, data=builds_htmls)


def branch_view(platform, name):
    return render_template('branch.html', platform=platform, name=name)


def test_report_view(platform, label, name):
    df_suites = get_test_suites(name)
    if df_suites is not None:
        # print(df_suites.iloc[0, :])
        df_suites = df_suites[(df_suites["status"] == "FAILED") | (df_suites["status"] == "REGRESSION")]

        df_suites = df_suites.sort_values(['className', 'name'], ascending=True)
        #TODO map className to Components
        cols = ["age", "status", "name", "T, s", "errorDetails"]
        suites_html = pd_to_html(df_suites, cols=cols, escape=True)
    else:
        suites_html = ""
    return render_template('test_report.html', platform=platform, label=label, name=name, suites_html=suites_html)
