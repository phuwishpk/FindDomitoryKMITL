# app/core/context_processors.py
# ไฟล์นี้สำหรับส่งตัวแปรไปให้ Templates ทุกหน้า

from app.forms.upload import EmptyForm
from app.forms.owner import ROOM_TYPE_CHOICES
from flask import current_app

def inject_global_vars():
    """
    ส่งตัวแปรที่ใช้บ่อยๆ ไปยัง Jinja2 templates
    """
    # ใช้ current_app.extensions ที่นี่เพราะ app context พร้อมใช้งานแล้ว
    history_service = current_app.extensions["container"].get("history_service")
    recently_viewed = []
    if history_service:
        recently_viewed = history_service.get_viewed_properties()

    room_type_map = dict(ROOM_TYPE_CHOICES)
    
    return dict(
        empty_form=EmptyForm(),
        ROOM_TYPES=room_type_map,
        recently_viewed_properties=recently_viewed
    )
