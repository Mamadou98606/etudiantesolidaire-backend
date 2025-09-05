from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    database_url = os.environ.get('DATABASE_URL')
    # Normalize legacy scheme and force psycopg v3 driver for SQLAlchemy
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if database_url and database_url.startswith('postgresql://') and '+psycopg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    # Use writable ephemeral storage for SQLite fallback in containers
    if not database_url:
        database_url = 'sqlite:////tmp/app.db'

    # Add a short connect timeout for Postgres to avoid long hangs on startup
    if database_url.startswith('postgresql+psycopg://') and 'connect_timeout=' not in database_url:
        sep = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{sep}connect_timeout=5"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)

    # Log de diagnostic masqué pour confirmer la base utilisée
    try:
        masked = database_url
        if masked.startswith('postgresql+psycopg://'):
            masked = 'postgresql+psycopg://***:***@' + masked.split('@', 1)[1]
        print(f"[info] Using database: {masked}", flush=True)
    except Exception:
        pass

    # Ensure app still boots even if the database is temporarily unavailable
    try:
        with app.app_context():
            should_create = (
                database_url.startswith('sqlite:///') or
                database_url.startswith('sqlite:////') or
                os.environ.get('AUTO_CREATE_TABLES', 'false').lower() == 'true'
            )
            if should_create:
                db.create_all()
    except Exception as e:
        print(f"[warn] Database initialization skipped due to error: {e}", flush=True)
