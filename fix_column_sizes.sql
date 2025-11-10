-- Script de correction des tailles de colonnes PostgreSQL
-- Problème: Les colonnes VARCHAR(X) ont été créées avec taille 1 au lieu de X
-- Solution: Modifier tous les VARCHAR pour avoir les bonnes tailles

-- Vérifier d'abord les colonnes existantes
-- \d users

-- Corriger toutes les colonnes VARCHAR
ALTER TABLE users
  ALTER COLUMN username SET DATA TYPE VARCHAR(80),
  ALTER COLUMN email SET DATA TYPE VARCHAR(120),
  ALTER COLUMN password_hash SET DATA TYPE VARCHAR(255),
  ALTER COLUMN first_name SET DATA TYPE VARCHAR(50),
  ALTER COLUMN last_name SET DATA TYPE VARCHAR(50),
  ALTER COLUMN nationality SET DATA TYPE VARCHAR(50),
  ALTER COLUMN study_level SET DATA TYPE VARCHAR(50),
  ALTER COLUMN field_of_study SET DATA TYPE VARCHAR(100),
  ALTER COLUMN email_verification_token SET DATA TYPE VARCHAR(255);

-- Vérifier que les colonnes ont les bonnes tailles maintenant
-- \d users
