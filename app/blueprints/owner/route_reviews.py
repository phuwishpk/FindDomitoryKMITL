from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import bp
from app.core.decorators import owner_required
from app.forms.owner import RequestReviewDeletionForm
from app.models.property import Property

@bp.route("/property/<int:prop_id>/reviews")
@login_required
@owner_required
def property_reviews(prop_id: int):
    prop = Property.query.get_or_404(prop_id)
    if prop.owner_id != current_user.ref_id:
        flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
        return redirect(url_for('owner.dashboard'))

    review_repo = current_app.extensions["container"]["review_repo"]

    reviews = review_repo.get_by_property_id(prop_id) 

    form = RequestReviewDeletionForm()

    return render_template("owner/property_reviews.html", prop=prop, reviews=reviews, form=form)

@bp.route("/review/<int:review_id>/request-delete", methods=["POST"])
@login_required
@owner_required
def request_delete_review(review_id: int):
    form = RequestReviewDeletionForm()
    review = current_app.extensions["container"]["review_repo"].get(review_id)
    if not review:
        flash("ไม่พบรีวิวที่ต้องการ", "danger")
        return redirect(url_for('owner.dashboard'))

    if form.validate_on_submit():
        review_mgmt_svc = current_app.extensions["container"]["review_management_service"]
        try:
            review_mgmt_svc.request_deletion(
                owner_id=current_user.ref_id,
                review_id=review_id,
                reason=form.reason.data
            )
            flash("ส่งคำร้องขอลบคอมเมนต์สำเร็จแล้ว", "success")
        except (PermissionError, ValueError) as e:
            flash(str(e), "danger")
    else:
        flash("กรุณากรอกเหตุผลในการขอลบ (ขั้นต่ำ 10 ตัวอักษร)", "danger")

    return redirect(url_for('owner.property_reviews', prop_id=review.property_id))

@bp.route("/review-reports")
@login_required
@owner_required
def review_reports():
    report_repo = current_app.extensions["container"]["review_report_repo"]
    reports = report_repo.get_reports_by_owner(current_user.ref_id)
    return render_template("owner/review_reports.html", reports=reports)
