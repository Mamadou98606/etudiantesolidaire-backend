# Guide de Configuration - Système de Vérification d'Email

Ce document explique comment configurer le système de vérification d'email pour la plateforme Étudiant Solidaire.

## 📋 Vue d'ensemble

Quand un utilisateur s'inscrit, le système :
1. Crée un compte avec `email_verified = False`
2. Génère un token de vérification (valide 24h)
3. Envoie un email avec un lien de vérification via **Resend**
4. L'utilisateur clique sur le lien pour vérifier son email
5. Le compte est maintenant actif

## 🔧 Configuration Nécessaire

### Backend

#### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Vérifie que `resend==0.8.0` est dans requirements.txt**

#### 2. Configurer la base de données

La migration SQL pour ajouter les colonnes de vérification d'email a déjà été créée.

Applique la migration si ce n'est pas fait :

```bash
psql -U your_user -d your_database -f migration_add_email_verification.sql
```

#### 3. Configurer les variables d'environnement

Crée un fichier `.env` dans le répertoire racine du backend :

```bash
cp .env.example .env
```

Puis remplis les variables suivantes :

```
# REQUIS pour les emails
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxx  # Ta clé API Resend
FRONTEND_URL=https://etudiantesolidaire.com  # L'URL du frontend

# Autres configurations
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=une-clé-secrète-longue-et-complexe
```

#### 4. Obtenir une clé API Resend

1. Va sur [resend.com](https://resend.com)
2. Crée un compte (gratuit)
3. Génère une clé API
4. Copie-la dans `.env` sous `RESEND_API_KEY`

⚠️ **Important** : Sans cette clé, les emails ne seront pas envoyés, mais l'inscription continuera de fonctionner (en mode "silencieux").

### Frontend

#### 1. Configurer les variables d'environnement

Crée un fichier `.env` dans le répertoire racine du frontend :

```bash
cp .env.example .env
```

Configure l'URL de l'API backend :

```
# Production
VITE_API_BASE_URL=https://api.etudiantesolidaire.com

# Développement local
VITE_API_BASE_URL=http://localhost:5000
```

## 🔄 Flux Complet de Vérification

### 1. Inscription

```
[Utilisateur]
    ↓
[Soumet le formulaire d'inscription]
    ↓
[Frontend: POST /api/register]
    ↓
[Backend: Crée l'utilisateur + token de vérification]
    ↓
[Backend: Envoie email via Resend]
    ↓
[Frontend: Affiche modal "Vérifiez votre email"]
    ↓
[Email arrivé à l'utilisateur avec lien]
```

### 2. Vérification d'Email

```
[Utilisateur clique sur le lien dans l'email]
    ↓
[Ouvre: /verify-email?token=xxxxx]
    ↓
[Frontend: Appelle GET /api/verify-email/<token>]
    ↓
[Backend: Valide le token + marque email_verified=True]
    ↓
[Frontend: Affiche "✅ Email vérifié"]
    ↓
[Redirection vers l'accueil]
```

### 3. Renvoyer l'Email

```
[Utilisateur clique "Renvoyer l'email"]
    ↓
[Frontend: POST /api/resend-verification-email]
    ↓
[Backend: Génère nouveau token + envoie email]
    ↓
[Frontend: Affiche "Email renvoyé"]
```

## 📝 Endpoints API

### 1. POST `/api/register`
Crée un nouvel utilisateur et envoie l'email de vérification

**Request** :
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "csrf_token": "token..."
}
```

**Response (201)** :
```json
{
  "message": "Inscription réussie. Veuillez vérifier votre email.",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "email_verified": false,
    ...
  }
}
```

### 2. GET `/api/verify-email/<token>`
Valide le token et marque l'email comme vérifié

**Response (200)** :
```json
{
  "message": "Email vérifié avec succès !",
  "user": {
    "id": 1,
    "email_verified": true,
    ...
  }
}
```

### 3. POST `/api/resend-verification-email`
Renvoie l'email de vérification

**Request** :
```json
{
  "email": "john@example.com"
}
```

**Response (200)** :
```json
{
  "message": "Email de vérification renvoyé avec succès."
}
```

## 🧪 Test en Local

### Terminal 1 - Backend

```bash
cd etudiantesolidaire-backend
python app.py
```

Le backend s'exécute sur `http://localhost:5000`

### Terminal 2 - Frontend

```bash
cd etudiantesolidaire-frontend
npm run dev
```

Le frontend s'exécute sur `http://localhost:5173` (ou un autre port)

### Tester l'inscription

1. Accède à `http://localhost:5173`
2. Clique sur "S'inscrire"
3. Remplis le formulaire d'inscription
4. Clique sur "S'inscrire"
5. Tu devrais voir la modal "Vérifiez votre email"

### Voir les logs des emails

Sans `RESEND_API_KEY`, tu verras dans la console du backend :

```
⚠️ RESEND_API_KEY not set, skipping email to user@example.com
```

Avec la clé configurée :

```
✅ Email de vérification envoyé à user@example.com
```

## 🐛 Dépannage

### "Email de vérification non reçu"

1. **Vérifie que `RESEND_API_KEY` est configurée** dans le `.env` du backend
2. Consulte les logs du backend pour voir si l'email a été envoyé
3. Vérifie le dossier spam dans ta boîte mail
4. Utilise le bouton "Renvoyer l'email" dans la modal

### "Token expiré"

Les tokens de vérification expirent après **24 heures**. Demande un nouveau lien avec "Renvoyer l'email".

### "Token invalide"

Le token n'existe pas ou a déjà été utilisé. Crée un nouveau compte.

### Erreur de connexion API

Vérifie que :
1. Le backend s'exécute sur le bon port
2. `VITE_API_BASE_URL` dans le `.env` du frontend pointe vers le bon endpoint
3. Les CORS sont bien configurés (vérifiés dans `src/main.py`)

## 📚 Fichiers Modifiés

### Backend
- `src/routes/user.py` - Endpoints d'authentification et vérification
- `src/models/user.py` - Champs pour la vérification d'email
- `.env.example` - Variables d'environnement nécessaires

### Frontend
- `src/pages/VerifyEmail.jsx` - Nouvelle page pour traiter le token
- `src/App.jsx` - Route `/verify-email` ajoutée
- `src/services/authService.js` - Méthodes `verifyEmail()` et `resendVerificationEmail()`
- `src/contexts/AuthContext.jsx` - Gestion de l'état de vérification
- `src/components/EmailVerificationModal.jsx` - Modal de vérification
- `.env.example` - Variables d'environnement

## 📧 Email Template

L'email envoyé contient :
- Un bouton "Vérifier mon email" cliquable
- Le lien de vérification en texte
- Info : "Ce lien est valide pendant 24 heures"
- Avertissement si l'utilisateur n'a pas créé le compte

## ✅ Checklist de Configuration

- [ ] Installer `resend` dans le backend (`pip install resend`)
- [ ] Créer un compte sur [resend.com](https://resend.com)
- [ ] Obtenir la clé API Resend
- [ ] Créer `.env` dans le backend avec `RESEND_API_KEY`
- [ ] Configurer `FRONTEND_URL` dans le `.env` du backend
- [ ] Appliquer les migrations SQL (colonnes email_verified, etc.)
- [ ] Créer `.env` dans le frontend avec `VITE_API_BASE_URL`
- [ ] Tester l'inscription en local
- [ ] Vérifier les logs pour s'assurer que les emails sont envoyés

## 🚀 Déploiement

Lors du déploiement (Render, Vercel, etc.) :

1. **Backend (Render)** :
   - Ajoute `RESEND_API_KEY` dans les variables d'environnement
   - Ajoute `FRONTEND_URL` = ton URL frontend en production

2. **Frontend (Netlify/Vercel)** :
   - Ajoute `VITE_API_BASE_URL` = l'URL de ton API en production

---

**Questions ?** Consulte la documentation de [Resend](https://resend.com/docs) pour plus d'infos sur l'API d'email.
