# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

# Flask settings
import os
# FLASK_SERVER_NAME = '0.0.0.0:8888'
FLASK_DEBUG = False  # Do not use debug mode in production
SECRET_KEY = os.environ["SECRET_KEY"]

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

# SQLAlchemy settings
# SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
# SQLALCHEMY_TRACK_MODIFICATIONS = False

# Mongo DB settings
MONGO_DBNAME = "reporting"