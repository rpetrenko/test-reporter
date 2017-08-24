import logging.config
from flask import Flask, Blueprint, current_app, render_template, request
from server import settings
from server.api.jenkins.endpoints.sites import ns as jenkins_sites_namespace
from server.api.jenkins.endpoints.jobs import ns as jenkins_jobs_namespace
from server.api.jenkins.endpoints.builds import ns as jenkins_builds_namespace
from server.api.jenkins.endpoints.test_reports import ns as jenkins_test_reports_namespace
from server.api.jenkins.endpoints.stats import ns as jenkins_test_stats_namespace
from server.api.jenkins.endpoints.datas import ns as jenkins_datas_namespace
from server.api.jenkins.endpoints.labels import ns as jenkins_labels_namespace
from server.api.common import api
from server.db import db
import os
import argparse

# in future replace dist-flask with dist/ and place AngularJS front-end there
USE_ANGULAR = False

if USE_ANGULAR:
    app = Flask(__name__, static_folder='../dist')

    @app.route('/')
    def index():
        return current_app.send_static_file('index.html')
else:
    from server.fe_flask.views import home
    app = Flask(__name__,
                template_folder='fe_flask',
                static_folder='fe_flask/static')

    @app.route('/', methods=('GET', 'POST'))
    def index():
        return home()


logging_conf_file = os.path.abspath("server/logging.conf")
print(logging_conf_file)
logging.config.fileConfig(logging_conf_file)
log = logging.getLogger(__name__)


def configure_app(flask_app):
    flask_app.config.from_pyfile('settings.py', silent=True)

    # flask_app.config['MONGO_DBNAME'] = settings.MONGO_DBNAME
    # flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    # flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    # flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    # flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP


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
    api.add_namespace(jenkins_labels_namespace)
    flask_app.register_blueprint(blueprint)

    # bp_ui = Blueprint('fe_flask', __name__, url_prefix='/')
    # flask_app.register_blueprint(bp_ui)

    db.init_app(flask_app)


def reset_database(flask_app):
    log.info("Drop database")
    db.cx.drop_database(flask_app.config['MONGO_DBNAME'])


def main():
    parser = argparse.ArgumentParser()
    default_host = "localhost"
    default_port = "8888"
    parser.add_argument("-H", "--host",
                        help="Hostname of the Flask app [default %s]" % default_host,
                        default=default_host)
    parser.add_argument("-P", "--port",
                        help="Port for the Flask app [default %s]" % default_port,
                        default=default_port)
    args = parser.parse_args()

    initialize_app(app)

    reset_db = not True
    if reset_db:
        with app.app_context():
            reset_database(app)

    app.run(host=args.host,
            port=args.port,
            debug=settings.FLASK_DEBUG,
            threaded=True)


if __name__ == "__main__":
    main()
