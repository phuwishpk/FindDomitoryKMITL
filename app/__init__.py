# app/__init__.py
from flask import Flask, send_from_directory, jsonify
from .config import Config

# 1. ย้าย extensions Instances (ที่ยังไม่ init) มาไว้ข้างนอก
#    (ไฟล์ extensions.py ของคุณทำแบบนี้อยู่แล้ว ดีมาก)
from .core import extensions

def create_app(config_class=Config) -> Flask:
    """
    ฟังก์ชัน Factory สำหรับสร้าง Flask Application Instance
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # 2. โหลดการตั้งค่า (Config)
    #    (ใน pytest, นี่คือจุดที่ Test Config จาก conftest.py จะถูกโหลด)
    app.config.from_object(config_class)

    # 3. Initialize Extensions (จาก app/core/extensions.py)
    #    (Extensions จะถูก init ด้วย Config ที่ถูกต้องแล้ว)
    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    extensions.login_manager.init_app(app)
    extensions.babel_ext.init_app(app)
    extensions.limiter.init_app(app)
    extensions.csrf.init_app(app)

    # --- vvv [แก้ไข] ย้ายทุกอย่างที่เหลือเข้ามา "ข้างใน" vvv ---
    
    # 4. Import core modules (ที่ต้องใช้ app)
    #    (ณ จุดนี้, import dependencies จะปลอดภัยแล้ว เพราะ config โหลดแล้ว)
    from .core import dependencies, context_processors, cli
    from .utils.helpers import format_as_bangkok_time, from_json_string

    # 5. Import Blueprints
    from .blueprints.public import bp as public_bp
    from .blueprints.owner import bp as owner_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.api import bp as api_bp

    # 6. ลงทะเบียน Dependencies (จาก app/core/dependencies.py)
    with app.app_context():
        dependencies.register_dependencies(app)

    # 7. ลงทะเบียน Jinja Filters
    app.jinja_env.filters['to_bkk_time'] = format_as_bangkok_time
    app.jinja_env.filters['fromjson'] = from_json_string

    # 8. ลงทะเบียน Context Processors (จาก app/core/context_processors.py)
    app.context_processor(context_processors.inject_global_vars)

    # 9. ลงทะเบียน Blueprints (ตอนนี้ Routes/URL จะถูกสร้างขึ้นแล้ว)
    app.register_blueprint(public_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # 10. ลงทะเบียน CLI Commands (จาก app/core/cli.py)
    cli.register_commands(app)

    # 11. ลงทะเบียน Routes พื้นฐาน
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )

    @app.get("/health")
    def health():
        return jsonify({"ok": True})
    
    # --- ^^^ [สิ้นสุดการแก้ไข] ^^^ ---

    return app
