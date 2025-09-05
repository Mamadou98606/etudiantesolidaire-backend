# Configuration Railway - Authentification

## Problèmes résolus

### 1. Erreur de build Railway
**Problème** : L'import dans `app.py` était incorrect
**Solution** : 
- Changé `from main import app` vers `from main import create_app`
- Créé l'instance de l'app avec `app = create_app()`

### 2. Configuration des sessions
**Problème** : Les sessions ne persistaient pas sur Railway
**Solution** :
- Ajouté Flask-Session pour une meilleure gestion
- Configuré les sessions avec des fichiers système
- Ajouté des configurations de sécurité pour les cookies

### 3. Configuration Railway
**Améliorations** :
- Changé le healthcheck vers `/health`
- Ajouté des workers et timeout pour Gunicorn
- Optimisé la configuration de déploiement

## Variables d'environnement requises

Dans Railway, configurez ces variables :

```bash
DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your-secret-key-here
RAILWAY_ENVIRONMENT=production
```

## Endpoints d'authentification

### Inscription
```bash
POST /api/register
Content-Type: application/json

{
  "username": "nom_utilisateur",
  "email": "email@example.com",
  "password": "mot_de_passe",
  "first_name": "Prénom",
  "last_name": "Nom",
  "nationality": "Nationalité",
  "study_level": "Niveau d'études",
  "field_of_study": "Domaine d'études"
}
```

### Connexion
```bash
POST /api/login
Content-Type: application/json

{
  "username": "nom_utilisateur_ou_email",
  "password": "mot_de_passe"
}
```

### Profil utilisateur
```bash
GET /api/profile
```

### Déconnexion
```bash
POST /api/logout
```

## Test local

Pour tester localement :

1. Créer un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configurer les variables d'environnement :
```bash
export DATABASE_URL="sqlite:///app.db"
export SECRET_KEY="dev-secret-key"
```

3. Lancer l'application :
```bash
python app.py
```

4. Tester l'authentification :
```bash
python test_auth.py
```

## Déploiement Railway

1. Connectez votre repository GitHub à Railway
2. Configurez les variables d'environnement dans Railway
3. Railway détectera automatiquement la configuration Python
4. Le build devrait maintenant réussir

## Structure des fichiers

```
/
├── app.py                 # Point d'entrée Railway
├── railway.json          # Configuration Railway
├── requirements.txt      # Dépendances Python
├── .env.example         # Variables d'environnement
├── test_auth.py         # Script de test
└── src/
    ├── main.py          # Application Flask principale
    ├── database/
    │   └── db.py        # Configuration base de données
    ├── models/
    │   └── user.py      # Modèles utilisateur
    └── routes/
        └── user.py      # Routes d'authentification
```

## Notes importantes

- Les sessions sont maintenant persistantes avec Flask-Session
- La configuration CORS est optimisée pour Railway
- Le healthcheck utilise l'endpoint `/health`
- Les cookies de session sont sécurisés en production