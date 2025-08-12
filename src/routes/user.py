from flask import Blueprint, jsonify, request, session
from src.models.user import User, UserProgress, UserBookmark, db
from datetime import datetime
import re

user_bp = Blueprint('user', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Validation des données
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email et password sont requis'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Format email invalide'}), 400
        
        if not validate_password(data['password']):
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Cet email est déjà utilisé'}), 400
        
        # Créer le nouvel utilisateur
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
        
        db.session.add(user)
        db.session.commit()
        
        # Créer la session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Inscription réussie',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'inscription'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username et password sont requis'}), 400
        
        # Chercher l'utilisateur par username ou email
        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Identifiants incorrects'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Compte désactivé'}), 401
        
        # Mettre à jour la dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Créer la session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Connexion réussie',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
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
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.json
        
        # Mise à jour des champs autorisés
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
        
        # Mise à jour email avec validation
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'error': 'Format email invalide'}), 400
            
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Cet email est déjà utilisé'}), 400
            
            user.email = data['email']
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@user_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.json
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Mot de passe actuel et nouveau mot de passe requis'}), 400
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
        
        if not validate_password(data['new_password']):
            return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères'}), 400
        
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Mot de passe modifié avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors du changement de mot de passe'}), 500

# Routes pour le suivi des progrès
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
        data = request.json
        
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'ajout du progrès'}), 500

# Routes pour les favoris
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
        data = request.json
        
        bookmark = UserBookmark(
            user_id=session['user_id'],
            title=data['title'],
            url=data['url'],
            category=data['category']
        )
        
        db.session.add(bookmark)
        db.session.commit()
        
        return jsonify(bookmark.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'ajout du favori'}), 500

@user_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        bookmark = UserBookmark.query.filter_by(
            id=bookmark_id, 
            user_id=session['user_id']
        ).first()
        
        if not bookmark:
            return jsonify({'error': 'Favori non trouvé'}), 404
        
        db.session.delete(bookmark)
        db.session.commit()
        
        return jsonify({'message': 'Favori supprimé'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@user_bp.route('/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            }), 200
    
    return jsonify({'authenticated': False}), 200
# ========================================
# ROUTE À AJOUTER DANS LE BACKEND
# ========================================
# 
# INSTRUCTIONS :
# 1. Ouvrir le fichier "src/routes/user.py" de votre backend
# 2. Ajouter ce code À LA FIN du fichier (avant la dernière ligne)
# 3. Sauvegarder
# 4. Redéployer sur Render
#
# ========================================

# Route pour lister tous les utilisateurs (à ajouter à la fin de user.py)
@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """
    Route pour récupérer la liste de tous les utilisateurs inscrits
    Accessible via GET /users
    """
    try:
        # Récupérer tous les utilisateurs de la base de données
        users = User.query.all()
        
        # Convertir les utilisateurs en format JSON (sans les mots de passe)
        users_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'nationality': user.nationality,
                'study_level': user.study_level,
                'field_of_study': user.field_of_study,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None,
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
            users_list.append(user_data)
        
        return jsonify({
            'success': True,
            'count': len(users_list),
            'users': users_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des utilisateurs: {str(e)}'
        }), 500


# ========================================
# COMMENT UTILISER CETTE ROUTE :
# ========================================
# 
# Une fois ajoutée et déployée, vous pourrez voir tous vos utilisateurs en allant sur :
# https://etudiantesolidaire-backend.onrender.com/users
# 
# La réponse sera au format JSON avec :
# - success: true/false
# - count: nombre d'utilisateurs
# - users: liste des utilisateurs avec leurs informations (sans mot de passe)
#
# ========================================

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401

    # Récupérer l'utilisateur connecté
    user = User.query.get(session['user_id'])

    # Vérifier que c'est un admin
    if not user or not getattr(user, 'is_admin', False):
        return jsonify({'error': 'Accès refusé'}), 403

    try:
        users = User.query.all()
        users_list = [u.to_dict() for u in users]  # utilise la méthode to_dict() du modèle User
        return jsonify({
            'success': True,
            'count': len(users_list),
            'users': users_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



