from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    database_url = os.environ.get('DATABASE_URL')

    # Normaliser l'ancien schéma et forcer le driver psycopg v3 pour SQLAlchemy
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if database_url and database_url.startswith('postgresql://') and '+psycopg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    # Fallback SQLite si pas de DATABASE_URL (en conteneur)
    if not database_url:
        database_url = 'sqlite:////tmp/app.db'

    # Éviter les blocages si Postgres ne répond pas
    if database_url.startswith('postgresql+psycopg://') and 'connect_timeout=' not in database_url:
        sep = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{sep}connect_timeout=5"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # SECRET_KEY doit être défini en tant que variable d'environnement
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
            raise ValueError("SECRET_KEY environment variable must be set in production")
        secret_key = 'dev-secret-key-not-for-production'
    app.config['SECRET_KEY'] = secret_key

    db.init_app(app)

    # Log masqué pour confirmer la base utilisée
    try:
        masked = database_url
        if masked.startswith('postgresql+psycopg://'):
            masked = 'postgresql+psycopg://***:***@' + masked.split('@', 1)[1]
        print(f"[info] Using database: {masked}", flush=True)
    except Exception:
        pass

    # Ne bloque pas le démarrage si la DB est indisponible
    try:
        with app.app_context():
            db.create_all()

            # ============ ÉTAPE 6 : Migration pour ajouter colonnes email ============
            # Ajouter les colonnes email_verified si elles n'existent pas
            try:
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE'))
                db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255) UNIQUE'))
                db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS email_token_expires_at TIMESTAMP'))
                db.session.commit()
                print("[info] Email verification columns ensured in database", flush=True)
            except Exception as e:
                db.session.rollback()
                print(f"[warn] Could not ensure email columns: {e}", flush=True)
            # ============ FIN ÉTAPE 6 ============
    except Exception as e:
        print(f"[warn] Database initialization skipped due to error: {e}", flush=True)
