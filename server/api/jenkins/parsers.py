# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

from flask_restplus import reqparse


get_args = reqparse.RequestParser()
get_args.add_argument('data_only',
                      type=int,
                      required=False,
                      default=None,
                      choices=[0, 1],
                      help="Get only records with data")
get_args.add_argument('last',
                      type=int,
                      required=False,
                      default=0,
                      help="Get only records N-latest results")
get_args.add_argument('data_fields',
                      type=str,
                      default='*',
                      required=False,
                      help="Populate records with the specified data fields")
get_args.add_argument('names',
                      type=str,
                      default=None,
                      required=False,
                      help="Get only results by build names")


get_data_args = reqparse.RequestParser()
get_data_args.add_argument('data_fields',
                           type=str,
                           default='*',
                           required=False,
                           help="Populate records with the specified data fields")
get_data_args.add_argument('ts_from',
                           type=int,
                           required=False,
                           help="Timestamp from")
get_data_args.add_argument('ts_to',
                           type=int,
                           required=False,
                           help="Timestamp to")

get_artifacts_args = reqparse.RequestParser()
get_artifacts_args.add_argument('search',
                                type=str,
                                required=False,
                                help="List of file patterns to fetch build artifacts")

get_jobs_args = reqparse.RequestParser()
get_jobs_args.add_argument('label',
                           type=str,
                           required=False,
                           default=None,
                           help="Get only jobs with label")

get_build_args = reqparse.RequestParser()
get_build_args.add_argument('job_label',
                            type=str,
                            required=False,
                            help="Get only builds for given JOB LABEL")
get_build_args.add_argument('data_fields',
                            type=str,
                            required=False,
                            help="Populate with datafields")
get_build_args.add_argument('building',
                            type=int,
                            required=False,
                            help="Status of the build 1-building, 0-not building")

get_cases_args = reqparse.RequestParser()
get_cases_args.add_argument('cases_fields',
                            type=str,
                            required=False,
                            help="Get only specific fields for testcases")
