# API Etudiant Solidaire

API Flask pour l'application Etudiant Solidaire avec authentification utilisateur.

## 🚀 Déploiement Railway

### 1. Configuration Railway

1. Connectez votre repository GitHub à Railway
2. Railway détectera automatiquement que c'est une application Python
3. Les variables d'environnement suivantes seront configurées automatiquement :
   - `DATABASE_URL` (PostgreSQL fourni par Railway)
   - `PORT` (port d'écoute)

### 2. Variables d'environnement requises

Dans le dashboard Railway, ajoutez ces variables :

```bash
SECRET_KEY=votre-cle-secrete-aleatoire-ici
```

### 3. Base de données

Railway fournira automatiquement une base de données PostgreSQL. L'application créera automatiquement les tables au premier démarrage.

## 🔐 Authentification

L'API fournit les endpoints suivants :

### Inscription
```bash
POST /api/register
Content-Type: application/json

{
  "username": "nom_utilisateur",
  "email": "email@example.com",
  "password": "motdepasse",
  "first_name": "Prénom",
  "last_name": "Nom",
  "nationality": "Française",
  "study_level": "Master",
  "field_of_study": "Informatique"
}
```

### Connexion
```bash
POST /api/login
Content-Type: application/json

{
  "username": "nom_utilisateur", // ou email
  "password": "motdepasse"
}
```

### Déconnexion
```bash
POST /api/logout
```

### Profil utilisateur
```bash
GET /api/profile
```

## 🏗️ Structure du projet

```
├── app.py                 # Point d'entrée Railway
├── railway.json          # Configuration Railway
├── Procfile              # Alternative pour Railway
├── requirements.txt      # Dépendances Python
├── runtime.txt          # Version Python
└── src/
    ├── main.py          # Application Flask principale
    ├── database/
    │   └── db.py        # Configuration base de données
    ├── models/
    │   └── user.py      # Modèles utilisateur
    └── routes/
        └── user.py      # Routes d'authentification
```

## 🔧 Développement local

1. Clonez le repository
2. Créez un environnement virtuel : `python3 -m venv venv`
3. Activez l'environnement : `source venv/bin/activate`
4. Installez les dépendances : `pip install -r requirements.txt`
5. Configurez les variables d'environnement dans un fichier `.env`
6. Lancez l'application : `python app.py`

## 📝 Notes

- L'application utilise des sessions Flask pour l'authentification
- La base de données PostgreSQL est configurée automatiquement sur Railway
- CORS est configuré pour permettre les requêtes depuis le frontend
- Les mots de passe sont hashés avec Werkzeug