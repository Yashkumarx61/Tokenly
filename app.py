import os
from flask import Flask, render_template, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import Config
from models import db, Business
from routes.auth import auth_bp
from routes.pos import pos_bp
from routes.admin import admin_bp
from routes.history import history_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    
    # Exempt API JSON routes from CSRF requirements for seamless API access
    csrf.exempt(auth_bp)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access your business POS terminal.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Business.query.get(int(user_id))

    # Initialize Rate Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[Config.RATELIMIT_DEFAULT],
        storage_uri=Config.RATELIMIT_STORAGE_URI
    )

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(history_bp)

    # Health Check Endpoint for CI/CD Automated Rollback Engine
    @app.route('/healthz')
    def health_check():
        try:
            # Verify DB Connection
            db.session.execute(db.text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'service': 'Tokenly POS',
                'database': 'connected'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    # Cinematic 3D Logo Reveal Animation Endpoint
    @app.route('/logo-reveal')
    def logo_reveal():
        return render_template('logo_reveal.html')

    # Centralized Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.error(f"Unhandled Exception: {str(e)}")
        if app.debug:
            raise e
        return render_template('errors/500.html'), 500

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
