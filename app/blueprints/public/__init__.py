# app/blueprints/public/__init__.py
from flask import Blueprint
bp = Blueprint("public", __name__)
from . import routes  # <-- เพิ่มบรรทัดนี้
