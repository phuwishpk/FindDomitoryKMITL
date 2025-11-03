# app/blueprints/auth/__init__.py
from flask import Blueprint
bp = Blueprint("auth", __name__, url_prefix="/auth") # <-- เพิ่ม url_prefix ที่นี่
