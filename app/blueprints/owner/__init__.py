# app/blueprints/owner/__init__.py
from flask import Blueprint

# 1. สร้าง Blueprint
bp = Blueprint("owner", __name__, url_prefix="/owner")
