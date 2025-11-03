# app/core/cli.py
# ไฟล์นี้สำหรับลงทะเบียนคำสั่ง Flask CLI

from flask import Flask
from app.models.property import Amenity
from app.models.user import Owner, Admin
from app.models.property import Property
from app.core.extensions import db
from werkzeug.security import generate_password_hash

def register_commands(app: Flask):
    """
    ลงทะเบียนคำสั่ง Command Line Interface (CLI)
    """

    @app.cli.command("seed_amenities")
    def seed_amenities():
        """
        เพิ่มข้อมูลสิ่งอำนวยความสะดวกเริ่มต้น
        """
        data = [
            ("pet","อนุญาตสัตว์เลี้ยง","Pets allowed"), ("ac","เครื่องปรับอากาศ","Air conditioning"),
            ("guard","รปภ.","Security guard"), ("cctv","กล้อง CCTV","CCTV"),
            ("fridge","ตู้เย็น","Refrigerator"), ("bed","เตียง","Bed"),
            ("heater","เครื่องทำน้ำอุ่น","Water heater"), ("internet","อินเทอร์เน็ต","Internet"),
            ("tv","ทีวี","TV"), ("sofa","โซฟา","Sofa"),
            ("wardrobe","ตู้เสื้อผ้า","Wardrobe"), ("desk","โต๊ะทำงาน","Desk"),
        ]
        for code, th, en in data:
            if not Amenity.query.filter_by(code=code).first():
                db.session.add(Amenity(code=code, label_th=th, label_en=en))
        db.session.commit()
        print("Seeded amenities ✅")

    @app.cli.command("seed_sample")
    def seed_sample():
        """
        เพิ่มข้อมูลตัวอย่าง (Admin, Owner, Property)
        """
        location_pin_data = {"type": "Point", "coordinates": [100.7758, 13.7292]}

        if not Owner.query.filter_by(email="owner@example.com").first():
            o = Owner(full_name_th="เจ้าของตัวอย่าง", citizen_id="1101700203451",
                      email="owner@example.com", password_hash=generate_password_hash("password"),
                      is_active=True, approval_status='approved') # Set owner as active
            db.session.add(o)
            db.session.commit()
            
            p = Property(owner_id=o.id, dorm_name="ตัวอย่างหอพัก", room_type="studio",
                         rent_price=6500,
                         location_pin=location_pin_data,
                         workflow_status=Property.WORKFLOW_APPROVED)
            db.session.add(p)
            db.session.commit()
            
        if not Admin.query.filter_by(username="admin").first():
            a = Admin(username="admin", password_hash=generate_password_hash("admin"), display_name="Administrator")
            db.session.add(a)
            db.session.commit()
        print("Seeded sample data ✅")
