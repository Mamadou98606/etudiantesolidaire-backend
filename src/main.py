import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from database.db import init_db
from routes.user import user_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration CORS pour Railway
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://etudiantesolidaire.com",
        "https://www.etudiantesolidaire.com"
    ])
    
    # Configuration des sessions pour Railway
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configuration Flask-Session pour Railway
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
    app.config['SESSION_FILE_THRESHOLD'] = 500
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'etudiant_solidaire:'
    
    # Initialiser Flask-Session
    Session(app)
    
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

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
