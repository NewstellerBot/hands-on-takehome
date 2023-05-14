from flask import (
    Blueprint,
    render_template,
)

from flaskr.auth import login_required

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/", methods=(["GET"]))
@login_required
def main():
    return render_template("dashboard/main.html")


@bp.route("/connect", methods=(["GET"]))
def connect():
    return render_template("dashboard/connect.html")
