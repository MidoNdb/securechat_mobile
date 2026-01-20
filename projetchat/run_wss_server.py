#!/usr/bin/env python
"""
═══════════════════════════════════════════════════════════
Script de lancement WebSocket Sécurisé (WSS)
═══════════════════════════════════════════════════════════
Lance Uvicorn avec support SSL/TLS pour développement local
Compatible Windows
"""
import os
import sys
from pathlib import Path

def main():
    """Lancer le serveur WSS avec Uvicorn"""
    
    # Chemins des certificats
    base_dir = Path(__file__).resolve().parent
    cert_path = base_dir / 'ssl_certificates' / 'cert.pem'
    key_path = base_dir / 'ssl_certificates' / 'key.pem'
    
    # Vérifier que les certificats existent
    if not cert_path.exists():
        print("❌ ERREUR: Certificat SSL non trouvé!")
        print(f"   Chemin attendu: {cert_path}")
        print("\n📝 Pour générer les certificats, exécutez:")
        print("   cd ssl_certificates")
        print("   python generate_ssl_cert.py")
        sys.exit(1)
    
    if not key_path.exists():
        print("❌ ERREUR: Clé privée SSL non trouvée!")
        print(f"   Chemin attendu: {key_path}")
        sys.exit(1)
    
    print("═══════════════════════════════════════════════════════════")
    print("🔒 Démarrage du serveur WebSocket Sécurisé (WSS)")
    print("═══════════════════════════════════════════════════════════")
    print(f"📁 Certificat: {cert_path}")
    print(f"🔑 Clé privée: {key_path}")
    print(f"🌐 URL WSS:    wss://127.0.0.1:8443/ws/chat/")
    print(f"🌐 URL HTTPS:  https://127.0.0.1:8443/")
    print("═══════════════════════════════════════════════════════════")
    print("⚠️  Certificat auto-signé : votre navigateur affichera un avertissement")
    print("   → Cliquez sur 'Avancé' puis 'Continuer vers le site'")
    print("═══════════════════════════════════════════════════════════")
    print("\n✅ Serveur prêt! Appuyez sur CTRL+C pour arrêter\n")
    
    try:
        import uvicorn
        
        # Lancer Uvicorn avec SSL (sans pré-charger Django)
        uvicorn.run(
            "apimessagerie.asgi:application",
            host="0.0.0.0",
            port=8443,
            ssl_keyfile=str(key_path),
            ssl_certfile=str(cert_path),
            log_level="info",
            reload=False,
            access_log=True,
            # Important: ne pas utiliser factory=True
        )
        
    except ImportError:
        print("\n❌ ERREUR: Uvicorn n'est pas installé")
        print("\n📦 Installation:")
        print("   pip install uvicorn")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Serveur arrêté")
        sys.exit(0)

if __name__ == '__main__':
    main()


# #!/usr/bin/env python
# """
# ═══════════════════════════════════════════════════════════
# Script de lancement WebSocket Sécurisé (WSS)
# ═══════════════════════════════════════════════════════════
# Lance Uvicorn avec support SSL/TLS pour développement local
# Compatible Windows
# """
# import os
# import sys
# from pathlib import Path

# def main():
#     """Lancer le serveur WSS avec Uvicorn"""
    
#     # Chemins des certificats
#     base_dir = Path(__file__).resolve().parent
#     cert_path = base_dir / 'ssl_certificates' / 'cert.pem'
#     key_path = base_dir / 'ssl_certificates' / 'key.pem'
    
#     # Vérifier que les certificats existent
#     if not cert_path.exists():
#         print("❌ ERREUR: Certificat SSL non trouvé!")
#         print(f"   Chemin attendu: {cert_path}")
#         print("\n📝 Pour générer les certificats, exécutez:")
#         print("   cd ssl_certificates")
#         print("   python generate_ssl_cert.py")
#         sys.exit(1)
    
#     if not key_path.exists():
#         print("❌ ERREUR: Clé privée SSL non trouvée!")
#         print(f"   Chemin attendu: {key_path}")
#         sys.exit(1)
    
#     print("═══════════════════════════════════════════════════════════")
#     print("🔒 Démarrage du serveur WebSocket Sécurisé (WSS)")
#     print("═══════════════════════════════════════════════════════════")
#     print(f"📁 Certificat: {cert_path}")
#     print(f"🔑 Clé privée: {key_path}")
#     print(f"🌐 URL WSS:    wss://127.0.0.1:8443/ws/chat/")
#     print(f"🌐 URL HTTPS:  https://127.0.0.1:8443/")
#     print("═══════════════════════════════════════════════════════════")
#     print("⚠️  Certificat auto-signé : votre navigateur affichera un avertissement")
#     print("   → Cliquez sur 'Avancé' puis 'Continuer vers le site'")
#     print("═══════════════════════════════════════════════════════════")
#     print("\n✅ Serveur prêt! Appuyez sur CTRL+C pour arrêter\n")
    
#     try:
#         import uvicorn
        
#         # Lancer Uvicorn avec SSL (sans pré-charger Django)
#         uvicorn.run(
#             "apimessagerie.asgi:application",
#             host="0.0.0.0",
#             port=8443,
#             ssl_keyfile=str(key_path),
#             ssl_certfile=str(cert_path),
#             log_level="info",
#             reload=False,
#             access_log=True,
#             # Important: ne pas utiliser factory=True
#         )
        
#     except ImportError:
#         print("\n❌ ERREUR: Uvicorn n'est pas installé")
#         print("\n📦 Installation:")
#         print("   pip install uvicorn")
#         sys.exit(1)
        
#     except KeyboardInterrupt:
#         print("\n\n🛑 Serveur arrêté")
#         sys.exit(0)

# if __name__ == '__main__':
#     main()