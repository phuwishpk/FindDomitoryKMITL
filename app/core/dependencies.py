# app/core/dependencies.py
# ไฟล์นี้ทำหน้าที่ตั้งค่า Dependency Injection Container

from flask import Flask
from app.repositories.sqlalchemy.user_repo_sql import SqlUserRepo
from app.repositories.sqlalchemy.property_repo_sql import SqlPropertyRepo
from app.repositories.sqlalchemy.approval_repo_sql import SqlApprovalRepo
from app.repositories.sqlalchemy.review_repo_sql import SqlReviewRepo
from app.repositories.sqlalchemy.review_report_repo_sql import SqlReviewReportRepo

from app.services.auth_service import AuthService
from app.services.property_service import PropertyService
from app.services.search_service import SearchService
from app.services.approval_service import ApprovalService
from app.services.upload_service import UploadService
from app.services.dashboard_service import DashboardService
from app.services.review_service import ReviewService
from app.services.review_management_service import ReviewManagementService
from app.services.history_service import HistoryService

def register_dependencies(app: Flask):
    """
    ลงทะเบียน Services และ Repositories ต่างๆ เข้าไปใน app context
    """
    container = {}
    container["user_repo"] = SqlUserRepo()
    container["property_repo"] = SqlPropertyRepo()
    container["approval_repo"] = SqlApprovalRepo()
    container["review_repo"] = SqlReviewRepo()
    container["review_report_repo"] = SqlReviewReportRepo()
    container["upload_service"] = UploadService(app.config.get("UPLOAD_FOLDER", "uploads"))
    container["auth_service"] = AuthService(
        user_repo=container["user_repo"],
        upload_service=container["upload_service"]
    )
    container["property_service"] = PropertyService(container["property_repo"])
    container["search_service"] = SearchService(container["property_repo"])
    container["approval_service"] = ApprovalService(container["approval_repo"], container["property_repo"])
    container["review_service"] = ReviewService(container["review_repo"])
    container["review_management_service"] = ReviewManagementService(
        review_repo=container["review_repo"],
        report_repo=container["review_report_repo"],
        prop_repo=container["property_repo"]
    )
    container["dashboard_service"] = DashboardService(
        user_repo=container["user_repo"],
        property_repo=container["property_repo"],
        approval_repo=container["approval_repo"],
        review_report_repo=container["review_report_repo"]
    )
    container["history_service"] = HistoryService(container["property_repo"])
    
    if not hasattr(app, "extensions"):
        app.extensions = {}
    app.extensions["container"] = container
