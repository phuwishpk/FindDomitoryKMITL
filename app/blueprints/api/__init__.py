# app/blueprints/api/__init__.py
from flask import Blueprint
bp = Blueprint("api", __name__, url_prefix="/api")

from . import routes # noqa: E402, F401
