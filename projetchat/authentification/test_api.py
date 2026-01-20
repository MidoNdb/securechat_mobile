# authentification/test_api.py

"""
Tests manuels pour l'API
Exécuter avec : python manage.py shell < authentification/test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

# ========================================
# COULEURS POUR AFFICHAGE
# ========================================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

# ========================================
# TEST 1 : REGISTER
# ========================================
def test_register():
    print_info("Test 1: Register")
    
    data = {
        "phone_number": "+33612345678",
        "password": "TestPassword123!",
        "display_name": "Test User",
        "email": "test@example.com",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\n-----END PUBLIC KEY-----",
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "device_name": "iPhone Test",
        "device_type": "ios"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=data)
    
    if response.status_code == 201:
        print_success("Register réussi")
        result = response.json()
        print(json.dumps(result, indent=2))
        return result['data']['tokens']
    else:
        print_error(f"Register échoué: {response.status_code}")
        print(response.json())
        return None

# ========================================
# TEST 2 : LOGIN
# ========================================
def test_login():
    print_info("Test 2: Login")
    
    data = {
        "phone_number": "+33612345678",
        "password": "TestPassword123!",
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
    }
    
    response = requests.post(f"{BASE_URL}/login/", json=data)
    
    if response.status_code == 200:
        print_success("Login réussi")
        result = response.json()
        return result['data']['tokens']
    else:
        print_error(f"Login échoué: {response.status_code}")
        print(response.json())
        return None

# ========================================
# TEST 3 : GET CURRENT USER
# ========================================
def test_me(access_token):
    print_info("Test 3: Get Current User")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/me/", headers=headers)
    
    if response.status_code == 200:
        print_success("Get user réussi")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Get user échoué: {response.status_code}")

# ========================================
# TEST 4 : UPDATE PROFILE
# ========================================
def test_update_profile(access_token):
    print_info("Test 4: Update Profile")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "display_name": "Updated Name",
        "bio": "This is my bio"
    }
    
    response = requests.put(f"{BASE_URL}/profile/", json=data, headers=headers)
    
    if response.status_code == 200:
        print_success("Update profile réussi")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Update profile échoué: {response.status_code}")

# ========================================
# TEST 5 : GET SESSIONS
# ========================================
def test_sessions(access_token):
    print_info("Test 5: Get Active Sessions")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/sessions/", headers=headers)
    
    if response.status_code == 200:
        print_success("Get sessions réussi")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Get sessions échoué: {response.status_code}")

# ========================================
# TEST 6 : REFRESH TOKEN
# ========================================
def test_refresh(refresh_token):
    print_info("Test 6: Refresh Token")
    
    data = {
        "refresh": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/refresh/", json=data)
    
    if response.status_code == 200:
        print_success("Refresh réussi")
        return response.json()['data']
    else:
        print_error(f"Refresh échoué: {response.status_code}")
        return None

# ========================================
# TEST 7 : LOGOUT
# ========================================
def test_logout(access_token):
    print_info("Test 7: Logout")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(f"{BASE_URL}/logout/", headers=headers)
    
    if response.status_code == 200:
        print_success("Logout réussi")
    else:
        print_error(f"Logout échoué: {response.status_code}")

# ========================================
# EXÉCUTER TOUS LES TESTS
# ========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTS API SECURECHAT")
    print("="*60 + "\n")
    
    # Test 1: Register
    tokens = test_register()
    
    if tokens:
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        # Test 3: Get current user
        test_me(access_token)
        
        # Test 4: Update profile
        test_update_profile(access_token)
        
        # Test 5: Get sessions
        test_sessions(access_token)
        
        # Test 6: Refresh token
        new_tokens = test_refresh(refresh_token)
        if new_tokens:
            access_token = new_tokens['access']
        
        # Test 7: Logout
        test_logout(access_token)
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60 + "\n")