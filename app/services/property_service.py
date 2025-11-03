# app/services/property_service.py

from app.models.property import Property, Amenity
from .location_service import LocationDataHandler
# --- vvv [แก้ไข] ย้าย import มาไว้บนสุด vvv ---
from app.models.approval import AuditLog
from app.core.extensions import db
# --- ^^^ [สิ้นสุดการแก้ไข] ^^^ ---

class PropertyService:
    def __init__(self, repo):
        self.repo = repo
        self.location_handler = LocationDataHandler()

    def _prepare_data(self, data: dict) -> dict:
        """
        ฟังก์ชัน Helper เพื่อจัดการข้อมูลก่อนบันทึก
        """
        if data.get('room_type') == 'other':
            other_type = data.get('other_room_type', '').strip()
            if other_type:
                data['room_type'] = other_type
        data.pop('other_room_type', None)

        location_json_str = data.pop('location_pin_json', None)
        data['location_pin'] = self.location_handler.parse_geojson_string(location_json_str)

        # --- vvv [START แก้ไขส่วนนี้] vvv ---
        # แก้ไข: ตรวจสอบ None ก่อนเรียก .strip()
        line_id_val = data.get('line_id')
        if not line_id_val or line_id_val.strip() == '-':
            data['line_id'] = None
        else:
            data['line_id'] = line_id_val.strip()

        fb_url_val = data.get('facebook_url')
        if not fb_url_val or fb_url_val.strip() == '-':
            data['facebook_url'] = None
        else:
            data['facebook_url'] = fb_url_val.strip()
        # --- ^^^ [END แก้ไขส่วนนี้] ^^^ ---

        return data

    def create(self, owner_id: int, data: dict) -> Property:
        amenity_codes = data.pop('amenities', [])
        data.pop('images', None)
        
        prepared_data = self._prepare_data(data)

        prop = Property(owner_id=owner_id, **prepared_data)
        if amenity_codes:
            amenities = Amenity.query.filter(Amenity.code.in_(amenity_codes)).all()
            prop.amenities = amenities
        return self.repo.add(prop)

    def update(self, owner_id: int, prop_id: int, data: dict):
        # (ย้าย import ไปไว้บนสุดแล้ว)

        prop = self.repo.get(prop_id)
        if not prop or prop.owner_id != owner_id:
            return None

        was_approved = prop.workflow_status == Property.WORKFLOW_APPROVED

        amenity_codes = data.pop('amenities', [])
        data.pop('images', None)
        prepared_data = self._prepare_data(data)

        for k, v in prepared_data.items():
            setattr(prop, k, v)

        if amenity_codes:
            amenities = Amenity.query.filter(Amenity.code.in_(amenity_codes)).all()
            prop.amenities = amenities
        else:
            prop.amenities = []
        
        if was_approved:
            prop.workflow_status = Property.WORKFLOW_DRAFT

        log_entry = AuditLog.log(
            actor_type="owner",
            actor_id=owner_id,
            action="update_property",
            property_id=prop_id,
            meta={"details": "Owner updated property info."}
        )
        db.session.add(log_entry)

        self.repo.save(prop)
        return prop
