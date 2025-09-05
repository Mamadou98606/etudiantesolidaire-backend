from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    # Fallback SQLite (conteneur) si pas de DATABASE_URL
    if not database_url:
        database_url = 'sqlite:////tmp/app.db'

    # Évite les blocages au démarrage si Postgres ne répond pas
    if database_url.startswith('postgresql://') and 'connect_timeout=' not in database_url:
        sep = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{sep}connect_timeout=5"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)

    # Log masqué pour confirmer la base utilisée
    try:
        masked = database_url
        if masked.startswith('postgresql://'):
            masked = 'postgresql://***:***@' + masked.split('@', 1)[1]
        print(f"[info] Using database: {masked}", flush=True)
    except Exception:
        pass

    # Ne bloque pas le démarrage si la DB est indispo
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"[warn] Database initialization skipped due to error: {e}", flush=True)
