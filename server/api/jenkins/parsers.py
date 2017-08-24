from flask_restplus import reqparse


get_args = reqparse.RequestParser()
get_args.add_argument('data_only',
                      type=int,
                      required=False,
                      default=0,
                      choices=[0, 1],
                      help="Get only records with data")

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