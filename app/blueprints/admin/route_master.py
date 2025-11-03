from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import admin_required
from app.core.extensions import db
from app.models.property import Amenity
from app.models.approval import AuditLog
from app.forms.upload import EmptyForm
from app.forms.admin import AmenityForm

@bp.route("/amenities", methods=["GET"])
@login_required
@admin_required
def amenities():
    amenities_list = Amenity.query.order_by(Amenity.label_th.asc()).all()
    form, delete_form = AmenityForm(), EmptyForm()
    return render_template("admin/amenities.html", amenities=amenities_list, form=form, delete_form=delete_form)

@bp.route("/amenities/add", methods=["POST"])
@login_required
@admin_required
def add_amenity():
    form = AmenityForm()
    if form.validate_on_submit():
        code = form.code.data.lower().strip()
        if Amenity.query.filter_by(code=code).first():
            flash(f"Code '{code}' นี้มีอยู่ในระบบแล้ว", 'danger')
        else:
            new_amenity = Amenity(code=code, label_th=form.label_th.data, label_en=form.label_en.data)
            db.session.add(new_amenity)
            db.session.add(AuditLog.log("admin", current_user.ref_id, "add_amenity", meta={"code": code, "label_th": new_amenity.label_th}))
            db.session.commit()
            flash('เพิ่มสิ่งอำนวยความสะดวกใหม่เรียบร้อยแล้ว', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('admin.amenities'))

@bp.route("/amenities/<int:amenity_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_amenity(amenity_id: int):
    amenity, form = Amenity.query.get_or_404(amenity_id), AmenityForm()
    if form.validate_on_submit():
        amenity.label_th, amenity.label_en = form.label_th.data, form.label_en.data
        db.session.add(AuditLog.log("admin", current_user.ref_id, "edit_amenity", meta={"code": amenity.code, "label_th": amenity.label_th}))
        db.session.commit()
        flash(f"แก้ไข '{amenity.label_th}' เรียบร้อยแล้ว", "success")
    else:
        flash('ข้อมูลที่ส่งมาไม่ถูกต้อง', 'danger')
    return redirect(url_for('admin.amenities'))

@bp.route("/amenities/<int:amenity_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_amenity(amenity_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.amenities'))
    amenity = Amenity.query.get_or_404(amenity_id)
    label_th, code = amenity.label_th, amenity.code
    db.session.add(AuditLog.log("admin", current_user.ref_id, "delete_amenity", meta={"code": code, "label_th": label_th}))
    db.session.delete(amenity)
    db.session.commit()
    flash(f"ลบ '{label_th}' ออกจากระบบเรียบร้อยแล้ว", "success")
    return redirect(url_for('admin.amenities'))
