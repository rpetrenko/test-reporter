from flask_restplus import reqparse


get_args = reqparse.RequestParser()
get_args.add_argument('data_only',
                      type=int,
                      required=False,
                      default=0,
                      choices=[0, 1],
                      help="Get only records with data")
