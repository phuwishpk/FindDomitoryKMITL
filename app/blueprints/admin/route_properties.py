from flask import render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import admin_required
from app.extensions import db
from app.models.property import Property
from app.models.user import Owner
from app.models.approval import AuditLog
from app.forms.upload import EmptyForm
from app.forms.admin import AdminEditPropertyForm
from datetime import datetime

@bp.route("/properties")
@login_required
@admin_required
def properties():
    page, search_query = request.args.get("page", 1, type=int), request.args.get('q', None)
    prop_repo = current_app.extensions["container"]["property_repo"]
    pagination = prop_repo.list_all_paginated(search_query=search_query, page=page, per_page=15)
    delete_form = EmptyForm()
    return render_template("admin/properties.html", pagination=pagination, search_query=search_query, delete_form=delete_form)

@bp.route("/property/<int:prop_id>/view")
@login_required
@admin_required
def view_property(prop_id: int):
    prop = Property.query.get(prop_id)
    if not prop:
        flash(f"ไม่พบข้อมูลหอพัก ID: {prop_id} (อาจถูกลบออกจากระบบอย่างถาวรแล้ว)", "warning")
        return redirect(url_for('admin.properties'))
    owner = Owner.query.get(prop.owner_id)
    return render_template("admin/property_detail.html", prop=prop, owner=owner)

@bp.route("/property/<int:prop_id>/admin_edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_property(prop_id: int):
    prop = Property.query.get_or_404(prop_id)
    form = AdminEditPropertyForm(obj=prop)
    if form.validate_on_submit():
        prop.dorm_name = form.dorm_name.data
        prop.workflow_status = form.workflow_status.data
        db.session.add(AuditLog.log("admin", current_user.ref_id, "admin_edit_property", prop_id))
        db.session.commit()
        flash(f"อัปเดตข้อมูลหอพัก '{prop.dorm_name}' เรียบร้อยแล้ว", "success")
        return redirect(url_for('admin.properties'))
    return render_template("admin/edit_property.html", prop=prop, form=form)

@bp.route("/property/<int:prop_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_property(prop_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid CSRF token.", "danger")
        return redirect(url_for('admin.properties'))
    prop = Property.query.get_or_404(prop_id)
    prop.deleted_at = datetime.utcnow()
    db.session.add(AuditLog.log("admin", current_user.ref_id, "soft_delete_property", prop_id))
    db.session.commit()
    flash(f"ย้ายหอพัก '{prop.dorm_name}' ไปยังถังขยะแล้ว", "success")
    return redirect(url_for('admin.properties'))

@bp.route("/properties/trash")
@login_required
@admin_required
def deleted_properties():
    page = request.args.get("page", 1, type=int)
    prop_repo = current_app.extensions["container"]["property_repo"]
    pagination = prop_repo.get_deleted_properties_paginated(page=page, per_page=15)
    restore_form, delete_form = EmptyForm(), EmptyForm()
    return render_template("admin/deleted_properties.html", pagination=pagination, restore_form=restore_form, delete_form=delete_form)

@bp.route("/property/<int:prop_id>/restore", methods=["POST"])
@login_required
@admin_required
def restore_property(prop_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.deleted_properties'))
    prop = Property.query.get_or_404(prop_id)
    prop.deleted_at = None
    db.session.add(AuditLog.log("admin", current_user.ref_id, "restore_property", prop_id))
    db.session.commit()
    flash(f"กู้คืนหอพัก '{prop.dorm_name}' สำเร็จ", "success")
    return redirect(url_for('admin.deleted_properties'))

@bp.route("/property/<int:prop_id>/permanent_delete", methods=["POST"])
@login_required
@admin_required
def permanently_delete_property(prop_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.deleted_properties'))
    prop_repo = current_app.extensions["container"]["property_repo"]
    prop = prop_repo.get(prop_id)
    if prop:
        dorm_name = prop.dorm_name
        db.session.add(AuditLog.log("admin", current_user.ref_id, "permanent_delete_property", meta={"deleted_name": dorm_name, "property_id": prop_id}))
        prop_repo.delete(prop)
        flash(f"ลบหอพัก '{dorm_name}' ออกจากระบบอย่างถาวรแล้ว", "success")
    else:
        flash("ไม่พบหอพักที่ต้องการลบ", "warning")
    return redirect(url_for('admin.deleted_properties'))
