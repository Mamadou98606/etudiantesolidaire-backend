import os
from flask import Flask, request, make_response
from database.db import init_db, db
from routes.user import user_bp
from routes.rdv import rdv_bp

def create_app():
    app = Flask(__name__)

    # ============ CONFIGURATION SÉCURITÉ SESSION ============
    # Ces paramètres sécurisent les cookies de session
    app.config['SESSION_COOKIE_SECURE'] = True  # Envoie le cookie SEULEMENT en HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript ne peut pas accéder au cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Anti-CSRF: cookie marche SEULEMENT sur notre domaine
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # La session expire après 24 heures
    # ============ FIN CONFIGURATION SESSION ============

    # Liste des origines autorisées
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://etudiantesolidaire.com",
        "https://www.etudiantesolidaire.com",
        "https://lovely-empanada-61146c.netlify.app",
        "https://api.etudiantesolidaire.com"
    ]

    # Handler pour les requêtes OPTIONS (preflight)
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            origin = request.headers.get('Origin')
            response = make_response()
            response.status_code = 200

            if origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            # Autoriser tous les headers nécessaires incluant X-CSRF-Token
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'

            return response, 200
        return None

    # Ajouter les headers CORS à toutes les réponses
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            # Autoriser X-CSRF-Token pour les requêtes CSRF
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    init_db(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(rdv_bp, url_prefix='/api')

    @app.route('/')
    def home():
        return {"message": "API Etudiant Solidaire", "status": "running"}

    @app.route('/health')
    def health():
        return {"status": "healthy"}, 200

    @app.route('/migrate', methods=['POST'])
    def migrate_db():
        """Endpoint pour appliquer les migrations manuellement (temporaire)"""
        try:
            from sqlalchemy import text
            # Ajouter les colonnes email_verified
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255) UNIQUE'))
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_token_expires_at TIMESTAMP'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_email_verification_token ON users(email_verification_token)'))
            db.session.commit()
            return {"message": "Migration réussie - colonnes email ajoutées"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Migration échouée: {str(e)}"}, 500    return app

"""Module-level Flask application instance for WSGI servers (e.g., Gunicorn)."""
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
