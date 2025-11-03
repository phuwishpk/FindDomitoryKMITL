from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import admin_required
from app.forms.upload import EmptyForm

@bp.route("/reviews/deletion-queue")
@login_required
@admin_required
def review_deletion_queue():
    report_repo = current_app.extensions["container"]["review_report_repo"]
    reports = report_repo.get_pending_reports()
    return render_template("admin/review_deletion_queue.html", reports=reports, empty_form=EmptyForm())

@bp.route("/review-report/<int:report_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_review_deletion(report_id: int):
    form = EmptyForm()
    if form.validate_on_submit():
        review_mgmt_svc = current_app.extensions["container"]["review_management_service"]
        try:
            review_mgmt_svc.process_report(current_user.ref_id, report_id, approve=True)
            flash("อนุมัติการลบคอมเมนต์สำเร็จ", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "danger")
    return redirect(url_for('admin.review_deletion_queue'))

@bp.route("/review-report/<int:report_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_review_deletion(report_id: int):
    form = EmptyForm()
    if form.validate_on_submit():
        review_mgmt_svc = current_app.extensions["container"]["review_management_service"]
        try:
            review_mgmt_svc.process_report(current_user.ref_id, report_id, approve=False)
            flash("ปฏิเสธคำร้องขอลบคอมเมนต์สำเร็จ", "info")
        except (ValueError, PermissionError) as e:
            flash(str(e), "danger")
    return redirect(url_for('admin.review_deletion_queue'))
