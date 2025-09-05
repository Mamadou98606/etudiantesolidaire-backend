#!/usr/bin/env python3
"""
Script de test pour l'API d'authentification
"""
import requests
import json

# URL de base (remplacez par votre URL Railway)
BASE_URL = "http://localhost:5000"  # Changez pour votre URL Railway

def test_health():
    """Test du endpoint de santé"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_register():
    """Test d'inscription"""
    try:
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        response = requests.post(f"{BASE_URL}/api/register", json=data)
        print(f"✅ Register: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ Register failed: {e}")
        return False

def test_login():
    """Test de connexion"""
    try:
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/api/login", json=data)
        print(f"✅ Login: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def main():
    print("🧪 Test de l'API d'authentification")
    print("=" * 40)
    
    # Test de santé
    if not test_health():
        print("❌ L'API n'est pas accessible")
        return
    
    # Test d'inscription
    test_register()
    
    # Test de connexion
    test_login()
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()