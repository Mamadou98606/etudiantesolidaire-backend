import os
from flask import Flask
from flask_cors import CORS
from database.db import init_db
from routes.user import user_bp
from routes.rdv import rdv_bp
from email_utils import mail

def create_app():
    app = Flask(__name__)

    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://etudiantesolidaire.com",
        "https://www.etudiantesolidaire.com",
        "https://lovely-empanada-61146c.netlify.app",
        "https://api.etudiantesolidaire.com"
    ])

    # Configuration du mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', True)
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@etudiantesolidaire.com')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'contact@etudiantesolidaire.com')

    init_db(app)
    mail.init_app(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(rdv_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return {"message": "API Etudiant Solidaire", "status": "running"}

    @app.route('/health')
    def health():
        try:
            from database.db import db
            # Test la connexion à la DB
            db.session.execute('SELECT 1')
            return {"status": "healthy", "database": "connected"}, 200
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}, 503

    return app

"""Module-level Flask application instance for WSGI servers (e.g., Gunicorn)."""
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
