import logging.config
from flask import Flask, Blueprint
from server import settings
from server.api.jenkins.endpoints.sites import ns as jenkins_sites_namespace
from server.api.jenkins.endpoints.jobs import ns as jenkins_jobs_namespace
from server.api.jenkins.endpoints.builds import ns as jenkins_builds_namespace
from server.api.jenkins.endpoints.test_reports import ns as jenkins_test_reports_namespace
from server.api.jenkins.endpoints.stats import ns as jenkins_test_stats_namespace
from server.api.jenkins.endpoints.datas import ns as jenkins_datas_namespace
from server.api.common import api
from server.db import db
import os

app = Flask(__name__)
logging_conf_file = os.path.abspath("server/logging.conf")
print(logging_conf_file)
logging.config.fileConfig(logging_conf_file)
log = logging.getLogger(__name__)


def configure_app(flask_app):
    flask_app.config['SERVER_NAME'] = settings.FLASK_SERVER_NAME
    flask_app.config['MONGO_DBNAME'] = settings.MONGO_DBNAME
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP


def initialize_app(flask_app):
    configure_app(flask_app)

    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)

    api.add_namespace(jenkins_sites_namespace)
    api.add_namespace(jenkins_jobs_namespace)
    api.add_namespace(jenkins_builds_namespace)
    api.add_namespace(jenkins_test_reports_namespace)
    api.add_namespace(jenkins_test_stats_namespace)
    api.add_namespace(jenkins_datas_namespace)

    flask_app.register_blueprint(blueprint)

    db.init_app(flask_app)


def reset_database(flask_app):
    log.info("Drop database")
    db.cx.drop_database(flask_app.config['MONGO_DBNAME'])


def main():
    initialize_app(app)
    log.info('Starting development server at http://{}/api/'.format(app.config['SERVER_NAME']))

    reset_db = not True
    if reset_db:
        with app.app_context():
            reset_database(app)

    app.run(debug=settings.FLASK_DEBUG)


if __name__ == "__main__":
    main()
