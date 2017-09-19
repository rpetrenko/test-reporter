# This source code is licensed under the Apache license found in the
# LICENSE file in the root directory of this project.

import argparse
from flask import Flask, current_app, render_template
from settings import USE_ANGULAR


if USE_ANGULAR:
    app = Flask(__name__, static_folder='../dist')

    @app.route('/')
    def index():
        return current_app.send_static_file('index.html')
else:
    from views import home_view, platform_view, test_report_view
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    @app.route('/', methods=('GET', 'POST'))
    def index():
        return home_view()

    @app.route('/platform/<name>')
    def platform(name):
        return platform_view(name)

    @app.route('/platform/<platform>/label/<label>/test_report/<name>')
    def test_report(platform, label, name):
        return test_report_view(platform, label, name)


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

    app.run(host=args.host,
            port=int(args.port),
            debug=True,
            threaded=True)


if __name__ == "__main__":
    main()
