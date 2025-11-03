from flask import render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import admin_required
from app.core.extensions import db
from app.models.property import Property
from app.models.user import Owner
from app.models.approval import AuditLog
from app.forms.upload import EmptyForm
from app.forms.admin import AdminEditOwnerForm
from datetime import datetime

@bp.route("/owners")
@login_required
@admin_required
def owners():
    page, search_query = request.args.get("page", 1, type=int), request.args.get('q', None)
    user_repo = current_app.extensions["container"]["user_repo"]
    pagination = user_repo.list_all_owners_paginated(search_query=search_query, page=page, per_page=15)
    delete_form = EmptyForm()
    return render_template("admin/owners.html", pagination=pagination, search_query=search_query, delete_form=delete_form)

@bp.route("/owners/<int:owner_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_owner(owner_id: int):
    owner = Owner.query.get_or_404(owner_id)
    form = AdminEditOwnerForm() 

    if request.method == "GET":
        form.is_active.data = owner.is_active

    if form.validate_on_submit():
        new_is_active = form.is_active.data
        old_is_active = owner.is_active

        if new_is_active != old_is_active:
            owner.is_active = new_is_active
            action = "activate_owner" if new_is_active else "deactivate_owner"
            meta_detail = "Activated" if new_is_active else "Deactivated"
            db.session.add(AuditLog.log(
                "admin", current_user.ref_id, 
                action, 
                meta={"owner_id": owner_id, "owner_name": owner.full_name_th, "details": f"Account {meta_detail}"}
            ))
            db.session.commit()
            flash(f"อัปเดตสถานะการใช้งานของ '{owner.full_name_th}' เป็น {'ใช้งานอยู่' if new_is_active else 'ไม่ใช้งาน'} เรียบร้อยแล้ว", "success")
        else:
            flash(f"ไม่มีการเปลี่ยนแปลงสถานะการใช้งานของ '{owner.full_name_th}'", "info")

        return redirect(url_for('admin.edit_owner', owner_id=owner_id))

    return render_template("admin/edit_owner.html", form=form, owner=owner)

@bp.route("/owners/<int:owner_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_owner(owner_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.owners'))
    owner = Owner.query.get_or_404(owner_id)
    owner.deleted_at = datetime.utcnow()
    db.session.add(AuditLog.log("admin", current_user.ref_id, "soft_delete_owner", meta={"owner_id": owner_id, "owner_name": owner.full_name_th}))
    db.session.commit()
    flash(f"ย้ายข้อมูล Owner '{owner.full_name_th}' ไปยังถังขยะแล้ว", "success")
    return redirect(url_for('admin.owners'))

@bp.route("/owners/trash")
@login_required
@admin_required
def deleted_owners():
    page = request.args.get("page", 1, type=int)
    user_repo = current_app.extensions["container"]["user_repo"]
    pagination = user_repo.get_deleted_owners_paginated(page=page)
    restore_form, delete_form = EmptyForm(), EmptyForm()
    return render_template("admin/deleted_owners.html", pagination=pagination, restore_form=restore_form, delete_form=delete_form)

@bp.route("/owners/<int:owner_id>/restore", methods=["POST"])
@login_required
@admin_required
def restore_owner(owner_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.deleted_owners'))
    owner = Owner.query.get_or_404(owner_id)
    owner.deleted_at = None
    db.session.add(AuditLog.log("admin", current_user.ref_id, "restore_owner", meta={"owner_id": owner_id, "owner_name": owner.full_name_th}))
    db.session.commit()
    flash(f"กู้คืนข้อมูล Owner '{owner.full_name_th}' สำเร็จ", "success")
    return redirect(url_for('admin.deleted_owners'))

@bp.route("/owners/<int:owner_id>/permanent_delete", methods=["POST"])
@login_required
@admin_required
def permanently_delete_owner(owner_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.deleted_owners'))
    user_repo = current_app.extensions["container"]["user_repo"]
    owner = user_repo.get_owner_by_id(owner_id)
    if owner:
        owner_name = owner.full_name_th
        Property.query.filter_by(owner_id=owner.id).delete(synchronize_session=False)
        db.session.add(AuditLog.log("admin", current_user.ref_id, "permanent_delete_owner", meta={"deleted_name": owner_name, "owner_id": owner_id}))
        user_repo.permanently_delete_owner(owner)
        flash(f"ลบข้อมูล Owner '{owner_name}' และหอพักที่เกี่ยวข้องทั้งหมดออกจากระบบอย่างถาวรแล้ว", "success")
    else:
        flash("ไม่พบข้อมูล Owner", "warning")
    return redirect(url_for('admin.deleted_owners'))
