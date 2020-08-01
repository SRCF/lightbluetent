from flask import Blueprint, render_template

bp = Blueprint("home", __name__)

@bp.route("/")
def index():
    return render_template("home/index.html")

@bp.route("/login")
def login():
    return render_template("home/login.html")

@bp.route("/register")
def register():
    return render_template("home/register.html")

@bp.route("/<socname>")
def society_welcome(socname):
    return render_template("home/welcome.html", socname=socname)
