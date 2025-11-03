# app/blueprints/admin/route_approval.py
from flask import render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import admin_required
from app.models.property import Property
from app.models.user import Owner
from app.forms.upload import EmptyForm
from app.forms.admin import RejectForm
from app.core.extensions import db
from app.models.approval import AuditLog

# --- Property Approval Workflow ---
@bp.route("/queue")
@login_required
@admin_required
def queue():
    search_query = request.args.get('q', None)
    approval_repo = current_app.extensions["container"]["approval_repo"]
    pending_props = approval_repo.get_pending_properties(search_query=search_query)
    return render_template("admin/queue.html", properties=pending_props)

@bp.route("/property/<int:prop_id>/review", methods=["GET"])
@login_required
@admin_required
def review_property(prop_id: int):
    prop = Property.query.get_or_404(prop_id)
    if prop.workflow_status != Property.WORKFLOW_SUBMITTED:
        flash("This item is not in the approval queue.", "warning")
        return redirect(url_for("admin.queue"))
    owner = Owner.query.get(prop.owner_id)
    reject_form, approve_form = RejectForm(), EmptyForm()
    return render_template("admin/review.html", prop=prop, owner=owner, reject_form=reject_form, approve_form=approve_form)

@bp.route("/property/<int:prop_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve(prop_id: int):
    # --- vvv [นี่คือจุดที่แก้ไข] vvv ---
    # เปลี่ยนจาก EmptyForm(request.form) เป็น EmptyForm()
    if not EmptyForm().validate_on_submit():
    # --- ^^^ [สิ้นสุดการแก้ไข] ^^^ ---
        flash("CSRF Token is invalid.", "danger")
        return redirect(url_for("admin.queue"))

    approval_service = current_app.extensions["container"]["approval_service"]
    try:
        approval_service.approve_property(admin_id=current_user.ref_id, prop_id=prop_id, note=None)
        flash("Property approved successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.queue"))

@bp.route("/property/<int:prop_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject(prop_id: int):
    reject_form = RejectForm()
    if reject_form.validate_on_submit():
        approval_service = current_app.extensions["container"]["approval_service"]
        try:
            approval_service.reject_property(admin_id=current_user.ref_id, prop_id=prop_id, note=reject_form.note.data)
            flash("Property rejected successfully.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("admin.queue"))
    flash("Please provide a reason for rejection.", "danger")
    return redirect(url_for("admin.review_property", prop_id=prop_id))

# --- Owner Approval Workflow ---
@bp.route("/owners/queue")
@login_required
@admin_required
def owner_queue():
    user_repo = current_app.extensions["container"]["user_repo"]
    pending_owners = user_repo.get_pending_owners()
    return render_template("admin/owner_queue.html", pending_owners=pending_owners)

@bp.route("/owners/<int:owner_id>/review")
@login_required
@admin_required
def review_owner(owner_id: int):
    user_repo = current_app.extensions["container"]["user_repo"]
    owner = user_repo.get_owner_by_id(owner_id)
    return render_template("admin/review_owner.html", owner=owner)

@bp.route("/owners/<int:owner_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_owner(owner_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid CSRF token.", "danger")
        return redirect(url_for("admin.owner_queue"))

    user_repo = current_app.extensions["container"]["user_repo"]
    owner = user_repo.get_owner_by_id(owner_id)

    if owner and owner.approval_status == Owner.APPROVAL_PENDING:
        owner.is_active, owner.approval_status = True, Owner.APPROVAL_APPROVED
        db.session.add(AuditLog.log("admin", current_user.ref_id, "approve_owner", meta={"owner_id": owner_id, "owner_name": owner.full_name_th}))
        user_repo.save_owner(owner)
        flash(f"อนุมัติบัญชีของ {owner.full_name_th} สำเร็จ", "success")
    else:
        flash("ไม่สามารถดำเนินการได้", "danger")
    return redirect(url_for("admin.owner_queue"))

@bp.route("/owners/<int:owner_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_owner(owner_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid CSRF token.", "danger")
        return redirect(url_for("admin.owner_queue"))

    user_repo = current_app.extensions["container"]["user_repo"]
    owner = user_repo.get_owner_by_id(owner_id)

    if owner and owner.approval_status == Owner.APPROVAL_PENDING:
        owner.is_active, owner.approval_status = False, Owner.APPROVAL_REJECTED
        db.session.add(AuditLog.log("admin", current_user.ref_id, "reject_owner", meta={"owner_id": owner_id, "owner_name": owner.full_name_th}))
        user_repo.save_owner(owner)
        flash(f"ปฏิเสธบัญชีของ {owner.full_name_th} สำเร็จ", "success")
    else:
        flash("ไม่สามารถดำเนินการได้", "danger")
    return redirect(url_for("admin.owner_queue"))
