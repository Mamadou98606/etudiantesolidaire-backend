from datetime import datetime
from database.db import db


class RDV(db.Model):
    __tablename__ = 'rdv_reservations'

    id = db.Column(db.Integer, primary_key=True)

    # Informations personnelles
    prenom = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    pays = db.Column(db.String(50), nullable=False)

    # Détails du RDV
    type_rdv = db.Column(db.String(50), nullable=False)  # orientation, demarches, logement, etc.
    consultation_type = db.Column(db.String(20), nullable=False)  # visio, phone, presentiel
    sujet = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)

    # Date et heure
    date_rdv = db.Column(db.Date, nullable=False)
    heure_rdv = db.Column(db.String(5), nullable=False)  # Format HH:MM

    # Statut et métadonnées
    statut = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ID utilisateur si connecté (optionnel)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    # Notes admin
    notes_admin = db.Column(db.Text, nullable=True)

    # Confirmation email
    email_admin_sent = db.Column(db.Boolean, default=False)
    email_user_sent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<RDV {self.nom} {self.prenom} - {self.date_rdv} {self.heure_rdv}>'

    def to_dict(self):
        return {
            'id': self.id,
            'prenom': self.prenom,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone,
            'pays': self.pays,
            'type_rdv': self.type_rdv,
            'consultation_type': self.consultation_type,
            'sujet': self.sujet,
            'message': self.message,
            'date_rdv': self.date_rdv.isoformat() if self.date_rdv else None,
            'heure_rdv': self.heure_rdv,
            'statut': self.statut,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'email_admin_sent': self.email_admin_sent,
            'email_user_sent': self.email_user_sent,
        }
