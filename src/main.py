import os
from flask import Flask, request, make_response
from database.db import init_db
from routes.user import user_bp
from routes.rdv import rdv_bp

def create_app():
    app = Flask(__name__)

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
            response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', 'Content-Type,Authorization')
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
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
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

    return app

"""Module-level Flask application instance for WSGI servers (e.g., Gunicorn)."""
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
