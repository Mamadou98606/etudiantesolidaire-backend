from flask import Blueprint, jsonify, request, session
from models.user import User, UserProgress, UserBookmark
from database.db import db
from datetime import datetime, timedelta
import re
import os
import secrets
import resend
from jinja2 import Template

# Initialize Resend API key
resend.api_key = os.environ.get('RESEND_API_KEY')

user_bp = Blueprint('user', __name__)

# ============ RATE LIMITING ============
# Dictionnaire pour tracker les tentatives échouées : {username_or_ip: [timestamp1, timestamp2, ...]}
login_attempts = {}

def get_client_identifier():
    """Récupérer l'identifiant du client (IP)"""
    return request.remote_addr or request.headers.get('X-Forwarded-For', 'unknown').split(',')[0]

def check_rate_limit(identifier, max_attempts=5, window_minutes=5):
    """
    Vérifier si le client a dépassé la limite de tentatives.
    Retourne (is_limited: bool, remaining_time: int en secondes)
    """
    now = datetime.utcnow()
    window = timedelta(minutes=window_minutes)

    # Nettoyer les anciennes tentatives
    if identifier in login_attempts:
        login_attempts[identifier] = [
            attempt_time for attempt_time in login_attempts[identifier]
            if now - attempt_time < window
        ]

    # Vérifier si on a dépassé la limite
    if identifier in login_attempts and len(login_attempts[identifier]) >= max_attempts:
        # Calculer le temps avant que la première tentative sort de la fenêtre
        oldest_attempt = login_attempts[identifier][0]
        reset_time = oldest_attempt + window
        remaining_seconds = int((reset_time - now).total_seconds())
        return True, remaining_seconds

    return False, 0

def record_failed_attempt(identifier):
    """Enregistrer une tentative échouée"""
    now = datetime.utcnow()
    if identifier not in login_attempts:
        login_attempts[identifier] = []
    login_attempts[identifier].append(now)

def clear_attempts(identifier):
    """Effacer les tentatives après une connexion réussie"""
    if identifier in login_attempts:
        del login_attempts[identifier]

# ============ FIN RATE LIMITING ============

# ============ CSRF PROTECTION ============
def generate_csrf_token():
    """Générer un nouveau token CSRF"""
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

def get_csrf_token():
    """Récupérer le token CSRF de la session"""
    if 'csrf_token' not in session:
        generate_csrf_token()
    return session['csrf_token']

def validate_csrf_token(token_to_check):
    """Valider un token CSRF"""
    token_in_session = session.get('csrf_token')
    # Utiliser constant_time_compare pour éviter les timing attacks
    return token_in_session and secrets.compare_digest(token_in_session, token_to_check)

def require_csrf_token(f):
    """Décorateur pour exiger un token CSRF valide"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Le token peut venir du header ou du JSON body
        csrf_token = request.headers.get('X-CSRF-Token') or (request.get_json() or {}).get('csrf_token')

        if not csrf_token:
            return jsonify({'error': 'CSRF token manquant'}), 403

        if not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        return f(*args, **kwargs)
    return decorated_function

# ============ FIN CSRF PROTECTION ============

# ============ ÉTAPE 6 : EMAIL VERIFICATION ============
def send_verification_email(user_email: str, verification_token: str, user_name: str = ''):
    """Envoyer un email de vérification via Resend API"""
    try:
        resend_api_key = os.environ.get('RESEND_API_KEY')
        frontend_url = os.environ.get('FRONTEND_URL', 'https://etudiantesolidaire.com')

        if not resend_api_key:
            print(f"⚠️ RESEND_API_KEY not set, skipping email to {user_email}", flush=True)
            return True  # Retourner True pour ne pas bloquer l'inscription

        # Créer le lien de vérification
        verification_url = f"{frontend_url}/verify-email?token={verification_token}"

        # Email HTML
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Bienvenue sur Étudiant Solidaire ! 🎓</h2>
            <p>Bonjour {user_name},</p>
            <p>Merci de vous être inscrit sur notre plateforme. Pour activer votre compte, veuillez vérifier votre adresse email en cliquant sur le bouton ci-dessous.</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Vérifier mon email
                </a>
            </p>
            <p>Ou copiez ce lien dans votre navigateur :</p>
            <p><code>{verification_url}</code></p>
            <p>Ce lien est valide pendant 24 heures.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                Si vous n'avez pas créé ce compte, ignorez cet email.
            </p>
        </div>
        """

        resend.Emails.send({
            "from": "noreply@etudiantesolidaire.com",
            "to": user_email,
            "subject": "Vérifiez votre email - Étudiant Solidaire",
            "html": html_content
        })

        print(f"✅ Email de vérification envoyé à {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi d'email : {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return True  # Retourner True pour ne pas bloquer l'inscription même si email échoue

def generate_verification_token():
    """Générer un token de vérification email"""
    return secrets.token_urlsafe(32)

# ============ FIN ÉTAPE 6 : EMAIL VERIFICATION ============
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Valider que le mot de passe est suffisamment fort.
    Requis : 8+ caractères, 1 majuscule, 1 chiffre, 1 caractère spécial
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins 1 majuscule"
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins 1 chiffre"
    if not any(c in '!@#$%^&*()-_+=[]{}|;:,.<>?' for c in password):
        return False, "Le mot de passe doit contenir au moins 1 caractère spécial (!@#$%^&* etc)"
    return True, "OK"

def validate_email(email):
    """
    Valider le format de l'email avec une regex simple mais efficace.
    """
    # Regex RFC 5322 simplifiée mais robuste
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

@user_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token_endpoint():
    """Endpoint pour récupérer le token CSRF"""
    token = get_csrf_token()
    return jsonify({'csrf_token': token}), 200

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}

        # Valider le CSRF token
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email et password sont requis'}), 400
        if not validate_email(data['email']):
            return jsonify({'error': 'Format email invalide'}), 400

        # Valider le mot de passe (retourne un tuple)
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': "Ce nom d'utilisateur existe déjà"}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': "Cet email est déjà utilisé"}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            nationality=data.get('nationality', ''),
            study_level=data.get('study_level', ''),
            field_of_study=data.get('field_of_study', '')
        )
        user.set_password(data['password'])

        # ============ ÉTAPE 6 : Générer token de vérification ============
        verification_token = generate_verification_token()
        user.email_verified = False
        user.email_verification_token = verification_token
        user.email_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        # ============ FIN ÉTAPE 6 ============

        db.session.add(user)
        db.session.commit()

        # Envoyer l'email de vérification
        user_name = data.get('first_name', data.get('username', 'Utilisateur'))
        send_verification_email(user.email, verification_token, user_name)

        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({
            'message': 'Inscription réussie. Veuillez vérifier votre email.',
            'user': user.to_dict(),
            'email_verified': False
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de l'inscription : {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Erreur lors de l'inscription : {str(e)}"}), 500

@user_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Vérifier l'email de l'utilisateur avec le token"""
    try:
        user = User.query.filter_by(email_verification_token=token).first()

        if not user:
            return jsonify({'error': 'Token invalide ou expiré'}), 400

        # Vérifier si le token n'a pas expiré
        if user.email_token_expires_at:
            # Convertir en datetime si nécessaire
            expires_at = user.email_token_expires_at
            if not isinstance(expires_at, datetime):
                expires_at = datetime.fromisoformat(str(expires_at))

            if expires_at < datetime.utcnow():
                return jsonify({'error': 'Token expiré. Veuillez demander un nouveau lien de vérification.'}), 400

        # Marquer l'email comme vérifié
        user.email_verified = True
        user.email_verification_token = None
        user.email_token_expires_at = None
        db.session.commit()

        return jsonify({
            'message': 'Email vérifié avec succès !',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la vérification: {str(e)}'}), 500

@user_bp.route('/resend-verification-email', methods=['POST'])
def resend_verification_email():
    """Renvoyer l'email de vérification"""
    try:
        data = request.get_json() or {}
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email requis'}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        # Si déjà vérifié
        if user.email_verified:
            return jsonify({'message': 'Cet email est déjà vérifié.'}), 200

        # Générer un nouveau token
        verification_token = generate_verification_token()
        user.email_verification_token = verification_token
        user.email_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()

        # Envoyer l'email (non-bloquant)
        try:
            user_name = user.first_name or user.username
            send_verification_email(user.email, verification_token, user_name)
        except Exception as e:
            print(f"⚠️ Email non-envoyé mais token généré: {str(e)}", flush=True)

        return jsonify({'message': 'Email de vérification renvoyé avec succès.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur resend_verification_email: {str(e)}", flush=True)
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@user_bp.route('/login', methods=['POST'])

def login():
    try:
        data = request.get_json() or {}

        # Vérifier le CSRF token
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username et password sont requis'}), 400

        # Vérifier le rate limiting
        client_id = get_client_identifier()
        is_limited, remaining_time = check_rate_limit(client_id)
        if is_limited:
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            return jsonify({
                'error': f'Trop de tentatives échouées. Réessayez dans {minutes}m {seconds}s'
            }), 429

        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        if not user or not user.check_password(data['password']):
            # Enregistrer la tentative échouée
            record_failed_attempt(client_id)
            return jsonify({'error': 'Identifiants incorrects'}), 401
        if not user.is_active:
            record_failed_attempt(client_id)
            return jsonify({'error': 'Compte désactivé'}), 401

        # Connexion réussie : effacer les tentatives échouées
        clear_attempts(client_id)

        user.last_login = datetime.utcnow()
        db.session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'message': 'Connexion réussie', 'user': user.to_dict()}), 200
    except Exception:
        return jsonify({'error': 'Erreur lors de la connexion'}), 500

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    return jsonify(user.to_dict()), 200

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        data = request.get_json() or {}

        # Vérifier le CSRF token
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        data = request.get_json() or {}
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'nationality' in data:
            user.nationality = data['nationality']
        if 'study_level' in data:
            user.study_level = data['study_level']
        if 'field_of_study' in data:
            user.field_of_study = data['field_of_study']
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'error': 'Format email invalide'}), 400
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Cet email est déjà utilisé'}), 400
            user.email = data['email']

        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@user_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        data = request.get_json() or {}

        # Vérifier le CSRF token
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Mot de passe actuel et nouveau mot de passe requis'}), 400

        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Mot de passe actuel incorrect'}), 400

        # Valider le nouveau mot de passe (retourne un tuple)
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Mot de passe modifié avec succès'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors du changement de mot de passe'}), 500

@user_bp.route('/progress', methods=['GET'])
def get_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    progress = UserProgress.query.filter_by(user_id=session['user_id']).all()
    return jsonify([p.to_dict() for p in progress]), 200

@user_bp.route('/progress', methods=['POST'])
def add_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        data = request.get_json() or {}
        progress = UserProgress(
            user_id=session['user_id'],
            category=data['category'],
            step=data['step'],
            completed=data.get('completed', False),
            notes=data.get('notes', '')
        )
        if progress.completed:
            progress.completed_at = datetime.utcnow()
        db.session.add(progress)
        db.session.commit()
        return jsonify(progress.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': "Erreur lors de l'ajout du progrès"}), 500

@user_bp.route('/bookmarks', methods=['GET'])
def get_bookmarks():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    bookmarks = UserBookmark.query.filter_by(user_id=session['user_id']).all()
    return jsonify([b.to_dict() for b in bookmarks]), 200

@user_bp.route('/bookmarks', methods=['POST'])
def add_bookmark():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        data = request.get_json() or {}

        # Vérifier le CSRF token
        csrf_token = data.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        bookmark = UserBookmark(
            user_id=session['user_id'],
            title=data['title'],
            url=data['url'],
            category=data.get('category')
        )
        db.session.add(bookmark)
        db.session.commit()
        return jsonify(bookmark.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': "Erreur lors de l'ajout du favori"}), 500

@user_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        # Vérifier le CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        data = request.get_json() or {}
        if not csrf_token:
            csrf_token = data.get('csrf_token')
        if not csrf_token or not validate_csrf_token(csrf_token):
            return jsonify({'error': 'CSRF token invalide'}), 403

        bookmark = UserBookmark.query.filter_by(
            id=bookmark_id, user_id=session['user_id']
        ).first()
        if not bookmark:
            return jsonify({'error': 'Favori non trouvé'}), 404
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'message': 'Favori supprimé'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@user_bp.route('/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'authenticated': True, 'user': user.to_dict()}), 200
    return jsonify({'authenticated': False}), 200

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_admin', False):
        return jsonify({'error': 'Accès refusé'}), 403
    users = User.query.all()
    users_list = [u.to_dict() for u in users]
    return jsonify({'success': True, 'count': len(users_list), 'users': users_list}), 200

@user_bp.route('/admin/promote', methods=['POST'])
def promote_admin():
    token = request.headers.get('X-Setup-Token')
    if token != os.environ.get('ADMIN_SETUP_TOKEN'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error': 'username requis'}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    user.is_admin = True
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()}), 200
