import os
from flask import Flask
from flask_cors import CORS
from database.db import init_db
from routes.user import user_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration simple CORS
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://etudiantesolidaire.com",
        "https://www.etudiantesolidaire.com",
        "https://lovely-empanada-61146c.netlify.app"
    ])
    
    # Initialiser la base de données (Railway)
    init_db(app)
    
    # Enregistrer les routes
    app.register_blueprint(user_bp, url_prefix='/api')
    
    @app.route('/')
    def home():
        return {"message": "API Etudiant Solidaire", "status": "running"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    return app

"""Module-level Flask application instance for WSGI servers (e.g., Gunicorn)."""
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
