from flask import Blueprint, render_template, redirect, url_for

bp = Blueprint("home", __name__)

@bp.route('/')
def home():
    return render_template("home.html", text="hello, world")
