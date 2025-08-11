#!/usr/bin/env python3
"""
Point d'entrée principal pour Render
Importe l'application Flask depuis src/main_render.py
"""
import sys
import os

# Ajouter le répertoire src au Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importer l'application Flask
from main import app

if __name__ == '__main__':
    # Pour les tests locaux
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
