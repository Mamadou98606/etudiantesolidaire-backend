#!/usr/bin/env python3
"""
Script de test pour l'authentification
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000/api"  # Changez pour votre URL Railway

def test_register():
    """Test d'inscription"""
    print("=== Test d'inscription ===")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_login():
    """Test de connexion"""
    print("\n=== Test de connexion ===")
    data = {
        "username": "testuser",
        "password": "password123"
    }
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return session, response

def test_profile(session):
    """Test du profil utilisateur"""
    print("\n=== Test du profil ===")
    response = session.get(f"{BASE_URL}/profile")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_logout(session):
    """Test de déconnexion"""
    print("\n=== Test de déconnexion ===")
    response = session.post(f"{BASE_URL}/logout")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

if __name__ == "__main__":
    print("Test de l'authentification...")
    print(f"URL de base: {BASE_URL}")
    
    # Test d'inscription
    register_response = test_register()
    
    if register_response.status_code in [200, 201]:
        # Test de connexion
        session, login_response = test_login()
        
        if login_response.status_code == 200:
            # Test du profil
            test_profile(session)
            
            # Test de déconnexion
            test_logout(session)
        else:
            print("Échec de la connexion")
    else:
        print("Échec de l'inscription")