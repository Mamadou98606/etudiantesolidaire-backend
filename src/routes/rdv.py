from flask import Blueprint, jsonify, request
from models.rdv import RDV
from database.db import db
from datetime import datetime, timedelta
import os
import re
from email_utils import send_email_rdv_confirmation

rdv_bp = Blueprint('rdv', __name__)


def validate_email(email):
    """Valider le format email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_rdv_form(data):
    """Valider les données du formulaire RDV"""
    errors = {}

    # Champs requis
    if not data.get('prenom') or data['prenom'].strip() == '':
        errors['prenom'] = 'Prénom requis'

    if not data.get('nom') or data['nom'].strip() == '':
        errors['nom'] = 'Nom requis'

    if not data.get('email') or data['email'].strip() == '':
        errors['email'] = 'Email requis'
    elif not validate_email(data['email']):
        errors['email'] = 'Email invalide'

    if not data.get('pays') or data['pays'].strip() == '':
        errors['pays'] = 'Pays requis'

    if not data.get('type_rdv') or data['type_rdv'].strip() == '':
        errors['type_rdv'] = 'Type de RDV requis'

    if not data.get('consultation_type') or data['consultation_type'].strip() == '':
        errors['consultation_type'] = 'Type de consultation requis'

    if not data.get('date_rdv') or data['date_rdv'].strip() == '':
        errors['date_rdv'] = 'Date préférée requis'

    if not data.get('heure_rdv') or data['heure_rdv'].strip() == '':
        errors['heure_rdv'] = 'Heure préférée requis'

    return errors


def is_slot_available(date_str, time_str):
    """Vérifier si un créneau est disponible"""
    try:
        # Chercher s'il y a déjà une réservation confirmée à cette date/heure
        existing_rdv = RDV.query.filter(
            RDV.date_rdv == date_str,
            RDV.heure_rdv == time_str,
            RDV.statut.in_(['pending', 'confirmed'])
        ).first()

        return existing_rdv is None
    except Exception:
        return False


@rdv_bp.route('/rdv/reserver', methods=['POST'])
def reserver_rdv():
    """Créer une nouvelle réservation de RDV"""
    try:
        data = request.get_json() or {}

        # Valider les données
        errors = validate_rdv_form(data)
        if errors:
            return jsonify({'error': 'Données invalides', 'details': errors}), 400

        # Vérifier que le créneau est disponible
        if not is_slot_available(data['date_rdv'], data['heure_rdv']):
            return jsonify({
                'error': 'Ce créneau est déjà réservé',
                'details': {'slot': 'Ce créneau n\'est plus disponible. Veuillez en choisir un autre.'}
            }), 409

        # Créer la réservation
        rdv = RDV(
            prenom=data['prenom'],
            nom=data['nom'],
            email=data['email'],
            telephone=data.get('telephone', ''),
            pays=data['pays'],
            type_rdv=data['type_rdv'],
            consultation_type=data['consultation_type'],
            sujet=data.get('sujet', ''),
            message=data.get('message', ''),
            date_rdv=data['date_rdv'],
            heure_rdv=data['heure_rdv'],
            statut='pending',
            user_id=data.get('user_id')
        )

        db.session.add(rdv)
        db.session.commit()

        # Envoyer les emails
        try:
            send_email_rdv_confirmation(rdv)
            rdv.email_admin_sent = True
            rdv.email_user_sent = True
            db.session.commit()
        except Exception as e:
            print(f"Erreur lors de l'envoi des emails: {e}")
            # Ne pas bloquer la réservation si les emails ne s'envoient pas

        return jsonify({
            'success': True,
            'message': 'Réservation créée avec succès',
            'rdv': rdv.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la création de la réservation: {e}")
        return jsonify({'error': 'Erreur lors de la création de la réservation'}), 500


@rdv_bp.route('/rdv/disponibilites/<date>', methods=['GET'])
def get_disponibilites(date):
    """Récupérer les créneau occupés pour une date donnée"""
    try:
        # Récupérer toutes les réservations confirmées/pending pour cette date
        rdvs = RDV.query.filter(
            RDV.date_rdv == date,
            RDV.statut.in_(['pending', 'confirmed'])
        ).all()

        # Extraire les heures occupées
        heures_occupees = [rdv.heure_rdv for rdv in rdvs]

        return jsonify({
            'date': date,
            'heures_occupees': heures_occupees,
            'total_reservations': len(rdvs)
        }), 200

    except Exception as e:
        print(f"Erreur lors de la récupération des disponibilités: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des disponibilités'}), 500


@rdv_bp.route('/rdv/mes-reservations', methods=['GET'])
def mes_reservations():
    """Récupérer les réservations d'un utilisateur (optionnel si connecté)"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email requis'}), 400

        rdvs = RDV.query.filter_by(email=email).order_by(RDV.date_rdv.desc()).all()

        return jsonify({
            'reservations': [rdv.to_dict() for rdv in rdvs]
        }), 200

    except Exception as e:
        print(f"Erreur lors de la récupération des réservations: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500


@rdv_bp.route('/rdv/annuler/<int:rdv_id>', methods=['POST'])
def annuler_rdv(rdv_id):
    """Annuler une réservation"""
    try:
        rdv = RDV.query.get(rdv_id)
        if not rdv:
            return jsonify({'error': 'Réservation non trouvée'}), 404

        # Vérifier l'email (sécurité basique)
        email = request.get_json().get('email')
        if rdv.email != email:
            return jsonify({'error': 'Non autorisé'}), 401

        rdv.statut = 'cancelled'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Réservation annulée',
            'rdv': rdv.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'annulation: {e}")
        return jsonify({'error': 'Erreur lors de l\'annulation'}), 500
