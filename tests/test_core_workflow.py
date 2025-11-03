import pytest
from werkzeug.security import generate_password_hash
from app.core.extensions import db
from app.models.user import Owner, Admin
from app.models.property import Property

# --- Fixtures (ตัวช่วย) ---

@pytest.fixture
def admin_client(client):
    """
    สร้าง Admin 1 คน และคืนค่า client ที่ล็อกอินเป็น Admin คนนั้นแล้ว
    """
    admin_pass = "admin_password"
    admin = Admin(username="test_admin", password_hash=generate_password_hash(admin_pass))
    db.session.add(admin)
    db.session.commit()
    
    # ล็อกอิน
    client.post('/auth/login', data={'username': 'test_admin', 'password': admin_pass})
    yield client
    # (หลัง Test จบ client จะถูกล้างค่าโดย conftest.py)

@pytest.fixture
def approved_owner_client(client):
    """
    สร้าง Owner 1 คนที่ "อนุมัติแล้ว" และคืนค่า client ที่ล็อกอินเป็น Owner คนนั้นแล้ว
    """
    owner_email = "owner@test.com"
    owner_pass = "owner_password"
    owner = Owner(
        full_name_th="Test Owner",
        citizen_id="1111111111111", # (Test DB ไม่เช็คความถูกต้อง)
        email=owner_email,
        password_hash=generate_password_hash(owner_pass),
        is_active=True,
        approval_status='approved' # <-- อนุมัติแล้ว
    )
    db.session.add(owner)
    db.session.commit()

    # ล็อกอิน
    client.post('/auth/login', data={'username': owner_email, 'password': owner_pass})
    yield client

# --- Tests (การทดสอบจริง) ---

def test_public_user_can_see_approved_property(client):
    """
    [แกนที่ 1: SearchService] 
    ทดสอบว่า User ทั่วไป (Anonymous) สามารถเห็นหอพักที่ "อนุมัติแล้ว" ได้
    """
    # GIVEN: สร้างหอพักที่อนุมัติแล้ว 1 แห่ง
    prop = Property(
        owner_id=1, # (ไม่สำคัญใน Test นี้)
        dorm_name="หอพัก A (อนุมัติแล้ว)",
        room_type="studio",
        workflow_status=Property.WORKFLOW_APPROVED
    )
    # GIVEN: สร้างหอพักที่ยังไม่อนุมัติ 1 แห่ง
    draft_prop = Property(
        owner_id=2,
        dorm_name="หอพัก B (แบบร่าง)",
        room_type="standard",
        workflow_status=Property.WORKFLOW_DRAFT
    )
    db.session.add_all([prop, draft_prop])
    db.session.commit()

    # WHEN: User ทั่วไปเปิดหน้าค้นหา
    response = client.get("/search")

    # THEN: ควรเห็นหอพัก A แต่ไม่เห็นหอพัก B
    assert response.status_code == 200
    assert "หอพัก A (อนุมัติแล้ว)".encode('utf-8') in response.data
    assert "หอพัก B (แบบร่าง)".encode('utf-8') not in response.data

def test_full_approval_workflow(client, admin_client):
    """
    [แกนหลักที่ 2: Auth + Property + Approval]
    ทดสอบกระบวนการทั้งหมด: 
    1. Owner สมัคร
    2. Admin อนุมัติ Owner
    3. Owner ล็อกอิน และ สร้างหอพัก
    4. Owner ส่งหอพักให้อนุมัติ
    5. Admin อนุมัติหอพัก
    6. User ทั่วไป ต้องเห็นหอพักนี้
    """
    
    # 1. Owner สมัคร
    response = client.post('/auth/owner/register', data={
        'full_name_th': 'เจ้าของใหม่',
        'email': 'new_owner@reg.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'citizen_id': '1234567890121'
    }, follow_redirects=True)
    
    assert response.status_code == 200 # (Redirect ไปหน้า Login)
    
    # ตรวจสอบใน DB
    new_owner = Owner.query.filter_by(email='new_owner@reg.com').first()
    assert new_owner is not None
    assert new_owner.approval_status == 'pending'

    # 2. Admin อนุมัติ Owner (ใช้ admin_client ที่ล็อกอินไว้แล้ว)
    admin_response = admin_client.post(f'/admin/owners/{new_owner.id}/approve', follow_redirects=True)
    assert admin_response.status_code == 200
    db.session.refresh(new_owner) # ดึงข้อมูลใหม่จาก DB
    assert new_owner.approval_status == 'approved'
    assert new_owner.is_active is True

    # 3. Owner ล็อกอิน และ สร้างหอพัก
    # (ใช้ client ธรรมดา แต่เราจะล็อกอินเป็น new_owner)
    login_response = client.post('/auth/login', data={
        'username': 'new_owner@reg.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert "กลับสู่หน้าหลักเจ้าของหอพัก".encode('utf-8') in login_response.data
    
    # Owner สร้างหอพัก
    create_response = client.post('/owner/property/new', data={
        'dorm_name': 'หอพักของฉัน',
        'road': 'ลาดกระบัง',
        'soi': '1',
        'room_type': 'studio',
        'rent_price': 5000,
        'contact_phone': '0812345678',
        'water_rate': 18,
        'electric_rate': 8,
        'deposit_amount': 10000,
        'location_pin_json': '{"type": "Point", "coordinates": [100.77, 13.72]}',
        'amenities': 'wifi' # (ต้องมีอย่างน้อย 1)
    }, follow_redirects=True)
    
    assert create_response.status_code == 200
    new_prop = Property.query.filter_by(dorm_name='หอพักของฉัน').first()
    assert new_prop is not None
    assert new_prop.workflow_status == 'draft'

    # 4. Owner ส่งหอพักให้อนุมัติ
    submit_response = client.post(f'/owner/property/{new_prop.id}/submit', follow_redirects=True)
    assert submit_response.status_code == 200
    db.session.refresh(new_prop)
    assert new_prop.workflow_status == 'submitted'

    # 5. Admin อนุมัติหอพัก
    admin_approve_prop = admin_client.post(f'/admin/property/{new_prop.id}/approve', follow_redirects=True)
    assert admin_approve_prop.status_code == 200
    db.session.refresh(new_prop)
    assert new_prop.workflow_status == 'approved'

    # 6. User ทั่วไป ต้องเห็นหอพักนี้
    # (ใช้ client ธรรมดาที่ไม่ได้ล็อกอิน)
    public_response = client.get('/search')
    assert public_response.status_code == 200
    assert "หอพักของฉัน".encode('utf-8') in public_response.data
