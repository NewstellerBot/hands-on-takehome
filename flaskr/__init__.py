import os

from flask import Flask, redirect, url_for, render_template
from flask_socketio import SocketIO


socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    socketio.init_app(app)

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_pyfile(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from flaskr import db

    db.init_app(app)

    from flaskr import auth

    app.register_blueprint(auth.bp)

    from flaskr import dashboard

    app.register_blueprint(dashboard.bp)

    app.add_url_rule("/", endpoint="index")

    from flaskr import websockets

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.route("/test")
    def test():
        return render_template("test.html")

    return app
