# app/core/decorators.py
# ไฟล์นี้เก็บ Decorators สำหรับตรวจสอบสิทธิ์การเข้าถึง

from functools import wraps
from flask_login import current_user
from flask import request, redirect, url_for

def owner_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "owner":
            return redirect(url_for("auth.login", role="owner"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return redirect(url_for("auth.login", role="admin"))
        return f(*args, **kwargs)
    return wrapper
