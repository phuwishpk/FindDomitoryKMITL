from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from . import bp
from app.core.decorators import owner_required
from app.models.property import Property
from app.models.approval import ApprovalRequest, AuditLog
from app.core.extensions import db
from app.forms.upload import EmptyForm

@bp.get("/dashboard")
@login_required
@owner_required
def dashboard():
    props = Property.query.filter_by(owner_id=current_user.ref_id, deleted_at=None).all()
    rejected_notes = {}
    rejected_prop_ids = [p.id for p in props if p.workflow_status == 'rejected']
    if rejected_prop_ids:
        latest_requests_sq = db.session.query(
            ApprovalRequest.property_id,
            func.max(ApprovalRequest.id).label('max_id')
        ).filter(
            ApprovalRequest.property_id.in_(rejected_prop_ids)
        ).group_by(ApprovalRequest.property_id).subquery()
        notes_query = db.session.query(
            ApprovalRequest.property_id,
            ApprovalRequest.note
        ).join(
            latest_requests_sq,
            ApprovalRequest.id == latest_requests_sq.c.max_id
        ).filter(ApprovalRequest.note.isnot(None))
        rejected_notes = dict(notes_query.all())
    submit_form = EmptyForm()
    delete_form = EmptyForm()
    return render_template("owner/dashboard.html",
                           props=props,
                           submit_form=submit_form,
                           delete_form=delete_form,
                           rejected_notes=rejected_notes)

@bp.route("/trash")
@login_required
@owner_required
def trash():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = db.paginate(
        Property.query.filter(
            Property.owner_id == current_user.ref_id,
            Property.deleted_at.isnot(None)
        ).order_by(Property.deleted_at.desc()),
        page=page, per_page=per_page, error_out=False
    )
    restore_form = EmptyForm()
    delete_form = EmptyForm()
    return render_template("owner/trash.html", pagination=pagination, restore_form=restore_form, delete_form=delete_form)

@bp.post("/property/<int:prop_id>/restore")
@login_required
@owner_required
def restore_property(prop_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('owner.trash'))
    prop = Property.query.get_or_404(prop_id)
    if prop.owner_id != current_user.ref_id:
        flash("Permission denied.", "danger")
        return redirect(url_for("owner.trash"))
    prop.deleted_at = None
    db.session.add(AuditLog.log("owner", current_user.ref_id, "restore_property", prop_id))
    db.session.commit()
    flash(f"กู้คืนประกาศ '{prop.dorm_name}' สำเร็จ", "success")
    return redirect(url_for('owner.trash'))

@bp.post("/property/<int:prop_id>/permanent_delete")
@login_required
@owner_required
def permanently_delete_property(prop_id: int):
    if not EmptyForm().validate_on_submit():
        flash("Invalid request.", "danger")
        return redirect(url_for('owner.trash'))
    prop = Property.query.get_or_404(prop_id)
    if prop.owner_id != current_user.ref_id:
        flash("Permission denied.", "danger")
        return redirect(url_for("owner.trash"))
    dorm_name = prop.dorm_name
    db.session.add(AuditLog.log("owner", current_user.ref_id, "permanent_delete_property", meta={"deleted_name": dorm_name, "property_id": prop_id}))
    db.session.delete(prop)
    db.session.commit()
    flash(f"ลบประกาศ '{dorm_name}' ออกจากระบบอย่างถาวรแล้ว", "success")
    return redirect(url_for('owner.trash'))
