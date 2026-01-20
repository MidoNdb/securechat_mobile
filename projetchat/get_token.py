#!/usr/bin/env python
"""
═══════════════════════════════════════════════════════════
Script pour obtenir un JWT token
═══════════════════════════════════════════════════════════
"""
import requests
import json
import urllib3
import uuid

# Désactiver les avertissements SSL pour certificat auto-signé
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_token():
    """Obtenir un token JWT via l'API de login"""
    
    print("═══════════════════════════════════════════════════════════")
    print("🔑 Obtention du token JWT")
    print("═══════════════════════════════════════════════════════════")
    
    # Demander les identifiants
    phone = input("\n📱 Numéro de téléphone (ex: +22243122691): ").strip()
    
    # Ajouter le préfixe + si manquant
    if not phone.startswith('+'):
        phone = '+222' + phone
    
    password = input("🔒 Mot de passe: ").strip()
    
    # Générer ou utiliser un device_id
    print("\n📱 Device ID:")
    print("   1. Utiliser un device_id existant")
    print("   2. Générer un nouveau device_id")
    choice = input("Choix (1 ou 2): ").strip()
    
    if choice == "1":
        device_id = input("📋 Entrez votre device_id: ").strip()
    else:
        device_id = str(uuid.uuid4())
        print(f"📋 Device ID généré: {device_id}")
    
    # URL de l'API (HTTPS car le serveur tourne en SSL)
    url = "https://127.0.0.1:8443/api/auth/login/"
    
    # Données de login
    data = {
        "phone_number": phone,
        "password": password,
        "device_id": device_id
    }
    
    print(f"\n📡 Envoi de la requête à: {url}")
    print(f"📋 Données envoyées:")
    print(f"   - Téléphone: {phone}")
    print(f"   - Device ID: {device_id}")
    
    try:
        # Faire la requête (verify=False pour accepter le certificat auto-signé)
        response = requests.post(url, json=data, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ Login réussi!")
            print("═══════════════════════════════════════════════════════════")
            
            # Afficher la structure complète pour débugger
            print("\n📦 Réponse complète de l'API:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("═══════════════════════════════════════════════════════════")
            
            # Extraire le token selon la structure
            # Structure possible: {"data": {"access": "...", "refresh": "..."}} 
            # ou {"access": "...", "refresh": "..."}
            if 'data' in result and 'access' in result['data']:
                access_token = result['data']['access']
                refresh_token = result['data'].get('refresh', 'N/A')
            elif 'access' in result:
                access_token = result['access']
                refresh_token = result.get('refresh', 'N/A')
            elif 'tokens' in result and 'access' in result['tokens']:
                access_token = result['tokens']['access']
                refresh_token = result['tokens'].get('refresh', 'N/A')
            else:
                print("\n⚠️  Structure de réponse inattendue")
                print("Le token se trouve dans la réponse ci-dessus")
                return None
            
            print("\n🎟️  ACCESS TOKEN (copie ce token):")
            print("─" * 63)
            print(access_token)
            print("─" * 63)
            
            print("\n🔄 REFRESH TOKEN:")
            print("─" * 63)
            print(refresh_token)
            print("─" * 63)
            
            print("\n💾 Token sauvegardé dans 'token.txt'")
            with open('token.txt', 'w') as f:
                f.write(access_token)
            
            print("\n💾 Device ID sauvegardé dans 'device_id.txt'")
            with open('device_id.txt', 'w') as f:
                f.write(device_id)
            
            return access_token
            
        elif response.status_code == 400:
            print(f"\n❌ Erreur de validation: {response.status_code}")
            try:
                error = response.json()
                print(json.dumps(error, indent=2, ensure_ascii=False))
            except:
                print(response.text)
            return None
            
        elif response.status_code == 401:
            print(f"\n❌ Identifiants incorrects")
            print("   → Vérifiez votre numéro de téléphone et mot de passe")
            return None
            
        else:
            print(f"\n❌ Erreur de login: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur")
        print("   → Vérifiez que le serveur WSS est lancé")
        print("   → Commande: python run_wss_server.py")
        return None
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    token = get_token()
    
    if token:
        print("\n" + "═"*63)
        print("🚀 Prochaine étape:")
        print("   python test_wss.py")
        print("   Puis collez le token quand demandé")
        print("═"*63)