import os
from werkzeug.utils import secure_filename
from datetime import datetime
import cloudinary
import cloudinary.uploader

class UploadService:
    def __init__(self, root_dir: str):
        # root_dir ไม่ได้ใช้แล้ว แต่คงโครงสร้างเดิมไว้
        self.root = root_dir

    def save_image(self, owner_id: int, file_storage) -> str:
        """
        อัปโหลดไฟล์รูปภาพไปยัง Cloudinary และคืนค่าเป็น secure URL
        """
        if not file_storage or not file_storage.filename:
            raise ValueError("File storage is invalid")

        filename = secure_filename(file_storage.filename)
        
        # สร้าง folder path บน Cloudinary เพื่อจัดระเบียบไฟล์
        folder_path = f"finddorm/owner_{owner_id}/images"

        try:
            # อัปโหลดไฟล์ไปยัง Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_storage,
                folder=folder_path,
                # สร้างชื่อไฟล์ที่ไม่ซ้ำกันโดยใช้ timestamp
                public_id=f"{int(datetime.utcnow().timestamp())}_{os.path.splitext(filename)[0]}"
            )
            # ดึง URL ของไฟล์ที่อัปโหลดเสร็จแล้ว
            secure_url = upload_result.get('secure_url')
            if not secure_url:
                raise ValueError("Cloudinary did not return a secure URL.")
            return secure_url
        except Exception as e:
            # หากเกิดข้อผิดพลาด ให้แสดง log และส่ง error ออกไป
            print(f"Error uploading image to Cloudinary: {e}")
            raise IOError("Failed to upload image to cloud storage.") from e

    def save_document(self, owner_id: int, file_storage) -> str:
        """
        อัปโหลดไฟล์เอกสาร (PDF) ไปยัง Cloudinary และคืนค่าเป็น secure URL
        """
        if not file_storage or not file_storage.filename:
            raise ValueError("File storage is invalid")
            
        filename = secure_filename(file_storage.filename)
        folder_path = f"finddorm/owner_{owner_id}/documents"

        try:
            # อัปโหลดไฟล์ไปยัง Cloudinary (ระบุ resource_type="raw" สำหรับไฟล์ที่ไม่ใช่รูปภาพ)
            upload_result = cloudinary.uploader.upload(
                file_storage,
                folder=folder_path,
                public_id=f"{int(datetime.utcnow().timestamp())}_{os.path.splitext(filename)[0]}",
                resource_type="raw"
            )
            secure_url = upload_result.get('secure_url')
            if not secure_url:
                raise ValueError("Cloudinary did not return a secure URL for the document.")
            return secure_url
        except Exception as e:
            print(f"Error uploading document to Cloudinary: {e}")
            raise IOError("Failed to upload document to cloud storage.") from e