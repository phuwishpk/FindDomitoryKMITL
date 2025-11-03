# app/blueprints/admin/__init__.py
from flask import Blueprint, redirect, url_for
from flask_login import login_required
from app.core.decorators import admin_required

# 1. สร้าง Blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")

# 2. สร้าง route พื้นฐาน (ถ้ามี)
@bp.route("/")
@login_required
@admin_required
def index():
    return redirect(url_for("admin.dashboard"))

# 3. Import ไฟล์ routes ย่อยทั้งหมด
# (สำคัญมาก: เพื่อให้ Flask ลงทะเบียน @bp.route ที่อยู่ในไฟล์เหล่านี้)
from . import route_dashboard
from . import route_properties
from . import route_owners
from . import route_approval
from . import route_reviews
from . import route_master
