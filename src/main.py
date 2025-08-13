import os
import sys
from flask import Flask, send_from_directory, request, make_response
from flask_cors import CORS
from database.db import db
from routes.user import user_bp

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# 1) Domaines front stables depuis l'env (séparés par virgules)
origins_env = os.environ.get('FRONTEND_ORIGIN', '')
allowed_origins = [o.strip() for o in origins_env.split(',') if o.strip()]
if not allowed_origins:
    allowed_origins = ['https://www.etudiantesolidaire.com']

# 2) Autoriser automatiquement tous les previews Vercel (*.vercel.app)
allowed_origin_suffixes = ['.vercel.app']

def is_allowed_origin(origin: str) -> bool:
    return bool(origin) and (
        origin in allowed_origins or any(origin.endswith(suf) for suf in allowed_origin_suffixes)
    )

# CORS de base (pour les réponses simples)
CORS(
    app,
    supports_credentials=True,
    origins=allowed_origins,
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
)

# Forcer les bons headers CORS sur toutes les réponses (y compris preflight)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        # Pour que les proxies/browsers comprennent que l'origin varie
        vary = response.headers.get('Vary')
        response.headers['Vary'] = f"{vary}, Origin" if vary else "Origin"
    return response

# Répondre explicitement aux preflight OPTIONS sous /api/*
@app.route('/api/<path:_path>', methods=['OPTIONS'])
def cors_preflight(_path):
    response = make_response('', 204)
    origin = request.headers.get('Origin')
    if is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', 'Content-Type, Authorization')
        response.headers['Access-Control-Allow-Methods'] = request.headers.get('Access-Control-Request-Method', 'GET, POST, PUT, DELETE, OPTIONS')
        vary = response.headers.get('Vary')
        response.headers['Vary'] = f"{vary}, Origin" if vary else "Origin"
    return response

# Cookies cross-site (HTTPS requis en prod)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

app.register_blueprint(user_bp, url_prefix='/api')

# DB (Render PostgreSQL via psycopg v3)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    url = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
