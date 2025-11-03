# app/blueprints/owner/__init__.py
from flask import Blueprint

# 1. สร้าง Blueprint
bp = Blueprint("owner", __name__, url_prefix="/owner")

# 2. Import ไฟล์ routes ย่อยทั้งหมด
from . import route_dashboard
from . import route_properties
from . import route_images
from . import route_reviews
