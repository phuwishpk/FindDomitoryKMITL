# app/blueprints/owner/__init__.py
from flask import Blueprint

# 1. สร้าง Blueprint
bp = Blueprint("owner", __name__, url_prefix="/owner")

# 2. Import routes ของ owner ทั้งหมด
from . import route_dashboard, route_properties, route_images, route_reviews # noqa: E402, F401