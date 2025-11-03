from flask import request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from . import bp
from app.core.decorators import owner_required
from app.forms.upload import UploadImageForm
from app.models.property import Property, PropertyImage
from app.extensions import db

# Policy import
try:
    from app.services.policies.property_policy import PropertyPolicy
except Exception:
    class PropertyPolicy:
        MAX_IMAGES = 6

@bp.post("/property/<int:prop_id>/image")
@login_required
@owner_required
def upload_image(prop_id: int):
    prop = Property.query.get_or_404(prop_id)
    if prop.owner_id != current_user.ref_id:
        return redirect(url_for("owner.dashboard"))
    form = UploadImageForm()
    if form.validate_on_submit() and form.image.data and form.image.data[0].filename:
        upload_svc = current_app.extensions["container"]["upload_service"]
        for i, file_storage in enumerate(form.image.data):
            count = PropertyImage.query.filter_by(property_id=prop.id).count()
            if count >= PropertyPolicy.MAX_IMAGES:
                flash(f"อัปโหลดได้สูงสุด {PropertyPolicy.MAX_IMAGES} รูปเท่านั้น", "warning")
                break
            if file_storage:
                path = upload_svc.save_image(current_user.ref_id, file_storage)
                max_pos = (PropertyImage.query.with_entities(func.max(PropertyImage.position))
                           .filter_by(property_id=prop.id).scalar()) or 0
                img = PropertyImage(property_id=prop.id, file_path=path, position=max_pos + 1)
                db.session.add(img)
        db.session.commit()
        flash("อัปโหลดรูปสำเร็จ", "success")
    else:
        flash("กรุณาเลือกไฟล์รูปภาพ", "danger")
    return redirect(url_for("owner.edit_property", prop_id=prop.id, tab="images"))

@bp.post("/property/<int:prop_id>/images/reorder")
@login_required
@owner_required
def reorder_images(prop_id: int):
    prop = Property.query.get_or_404(prop_id)
    if prop.owner_id != current_user.ref_id:
        return jsonify({"success": False, "message": "Permission denied."}), 403

    data = request.get_json()
    image_ids = data.get('order')

    if not isinstance(image_ids, list):
        return jsonify({"success": False, "message": "Invalid data format."}), 400

    images = PropertyImage.query.filter(
        PropertyImage.property_id == prop.id,
        PropertyImage.id.in_(image_ids)
    ).all()

    id_to_image_map = {img.id: img for img in images}

    for i, img_id in enumerate(image_ids):
        if img_id in id_to_image_map:
            id_to_image_map[img_id].position = i + 1

    db.session.commit()
    return jsonify({"success": True, "message": "จัดเรียงรูปภาพสำเร็จ"})
