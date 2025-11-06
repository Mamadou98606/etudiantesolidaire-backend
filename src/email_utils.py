import os
from flask_mail import Mail, Message
from jinja2 import Template

# Configuration Flask-Mail (à ajouter dans main.py)
# app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
# app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
# app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', True)
# app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
# app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@etudiantesolidaire.com')

mail = Mail()


def send_email_rdv_confirmation(rdv):
    """Envoyer un email de confirmation au user et à l'admin"""

    # Email utilisateur
    user_subject = f"Confirmation de votre réservation - {rdv.date_rdv} à {rdv.heure_rdv}"
    user_template = """
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px;">
                <h2 style="color: #0066cc;">Confirmation de votre réservation</h2>

                <p>Bonjour {{ prenom }} {{ nom }},</p>

                <p>Votre demande de rendez-vous a été reçue avec succès !</p>

                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Détails de votre réservation</h3>
                    <p><strong>Type de consultation :</strong> {{ type_rdv }}</p>
                    <p><strong>Date :</strong> {{ date_rdv }}</p>
                    <p><strong>Heure :</strong> {{ heure_rdv }}</p>
                    <p><strong>Mode :</strong> {{ consultation_type }}</p>
                    {% if sujet %}<p><strong>Sujet :</strong> {{ sujet }}</p>{% endif %}
                </div>

                <p>Nous vous contacterons dans les 24h ouvrées pour confirmer votre rendez-vous.</p>

                <p><strong>Besoin d'aide ?</strong><br>
                Contactez-nous : contact@etudiantesolidaire.com ou +33 1 23 45 67 89</p>

                <hr style="margin-top: 30px; color: #ddd;">
                <p style="font-size: 12px; color: #999;">
                    © 2025 Étudiante Solidaire. Tous droits réservés.
                </p>
            </div>
        </body>
    </html>
    """

    # Email admin
    admin_subject = f"NOUVEAU RDV : {rdv.prenom} {rdv.nom} - {rdv.date_rdv} à {rdv.heure_rdv}"
    admin_template = """
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 2px solid #ff9900; padding: 20px;">
                <h2 style="color: #ff9900;">NOUVELLE RÉSERVATION RDV</h2>

                <div style="background-color: #fff8e6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Informations étudiant</h3>
                    <p><strong>Nom :</strong> {{ prenom }} {{ nom }}</p>
                    <p><strong>Email :</strong> {{ email }}</p>
                    <p><strong>Téléphone :</strong> {{ telephone or 'Non fourni' }}</p>
                    <p><strong>Pays :</strong> {{ pays }}</p>
                </div>

                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Détails du RDV</h3>
                    <p><strong>Type :</strong> {{ type_rdv }}</p>
                    <p><strong>Date :</strong> {{ date_rdv }}</p>
                    <p><strong>Heure :</strong> {{ heure_rdv }}</p>
                    <p><strong>Mode :</strong> {{ consultation_type }}</p>
                    <p><strong>Sujet :</strong> {{ sujet or 'Non spécifié' }}</p>
                </div>

                {% if message %}
                <div style="background-color: #f0f0f0; padding: 15px; border-left: 4px solid #0066cc;">
                    <h3>Message de l'étudiant</h3>
                    <p>{{ message }}</p>
                </div>
                {% endif %}

                <p style="color: #ff9900; font-weight: bold;">
                    Vous devez contacter cet étudiant pour confirmer le rendez-vous.
                </p>
            </div>
        </body>
    </html>
    """

    try:
        # Préparer les données pour les templates
        data = {
            'prenom': rdv.prenom,
            'nom': rdv.nom,
            'email': rdv.email,
            'telephone': rdv.telephone,
            'pays': rdv.pays,
            'type_rdv': rdv.type_rdv,
            'date_rdv': rdv.date_rdv.strftime('%d/%m/%Y') if rdv.date_rdv else '',
            'heure_rdv': rdv.heure_rdv,
            'consultation_type': rdv.consultation_type,
            'sujet': rdv.sujet,
            'message': rdv.message,
        }

        # Générer les emails HTML
        user_body = Template(user_template).render(**data)
        admin_body = Template(admin_template).render(**data)

        admin_email = os.environ.get('ADMIN_EMAIL', 'contact@etudiantesolidaire.com')

        # Envoyer email utilisateur
        msg_user = Message(
            subject=user_subject,
            recipients=[rdv.email],
            html=user_body
        )
        mail.send(msg_user)

        # Envoyer email admin
        msg_admin = Message(
            subject=admin_subject,
            recipients=[admin_email],
            html=admin_body
        )
        mail.send(msg_admin)

        print(f"Emails envoyés pour la réservation {rdv.id}")
        return True

    except Exception as e:
        print(f"Erreur lors de l'envoi des emails: {e}")
        return False
