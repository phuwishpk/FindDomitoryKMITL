from flask import render_template, request, current_app
from flask_login import login_required
from . import bp  # <-- Import bp จาก __init__.py
from app.core.decorators import admin_required

@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    dashboard_svc = current_app.extensions["container"]["dashboard_service"]

    stats = dashboard_svc.get_stats()
    pie_chart = dashboard_svc.get_pie_chart_data()
    line_chart = dashboard_svc.get_line_chart_data()
    workflow_chart = dashboard_svc.get_workflow_status_chart_data()
    room_type_pie_chart = dashboard_svc.get_room_type_pie_chart_data()

    return render_template(
        "admin/dashboard.html", 
        stats=stats, 
        pie_chart=pie_chart, 
        line_chart=line_chart,
        workflow_chart=workflow_chart,
        room_type_pie_chart=room_type_pie_chart
    )

@bp.route("/logs")
@login_required
@admin_required
def logs():
    page = request.args.get("page", 1, type=int)
    approval_repo = current_app.extensions["container"]["approval_repo"]
    pagination = approval_repo.list_logs(page=page)
    return render_template("admin/logs.html", pagination=pagination)
