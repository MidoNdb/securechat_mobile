#!/usr/bin/env python
"""
═══════════════════════════════════════════════════════════
Test de connexion WebSocket Sécurisé (WSS)
═══════════════════════════════════════════════════════════
"""
import asyncio
import websockets
import json
import ssl

async def test_wss_connection(token):
    """
    Tester la connexion WSS
    
    Args:
        token: Votre JWT access token
    """
    # URL WebSocket sécurisée
    uri = f"wss://127.0.0.1:8443/ws/chat/?token={token}"
    
    # Context SSL (ignore les certificats auto-signés)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    print("═══════════════════════════════════════════════════════════")
    print("🔒 Test de connexion WebSocket Sécurisé (WSS)")
    print("═══════════════════════════════════════════════════════════")
    print(f"📡 Connexion à: {uri}")
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("✅ Connexion WSS établie!")
            
            # Recevoir le message de confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            print("\n📨 Message de bienvenue reçu:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Tester un envoi de message
            print("\n" + "═"*63)
            print("📤 Test d'envoi de message...")
            
            test_action = {
                "action": "ping",
                "message": "Test de connexion WSS réussi!"
            }
            
            await websocket.send(json.dumps(test_action))
            print("✅ Message envoyé!")
            
            print("\n" + "═"*63)
            print("🎉 TOUS LES TESTS WSS SONT RÉUSSIS!")
            print("═"*63)
            print("\n💡 Votre serveur WebSocket Sécurisé fonctionne correctement!")
            print("   Vous pouvez maintenant l'utiliser dans votre application.")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Erreur de connexion: {e}")
        print("   → Vérifiez que le serveur WSS est lancé")
        print("   → Commande: python run_wss_server.py")
        
    except websockets.exceptions.InvalidMessage as e:
        print(f"\n❌ Token JWT invalide ou expiré: {e}")
        print("   → Obtenez un nouveau token via /api/auth/login/")
        
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ Erreur WebSocket: {e}")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Erreur JSON: {e}")
        
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔑 Configuration du test WSS")
    print("─" * 63)
    print("Pour obtenir un token JWT:")
    print("1. Utilisez votre endpoint de login: POST /api/auth/login/")
    print("2. Copiez le 'access' token de la réponse")
    print("─" * 63)
    
    token = input("\n📋 Collez votre JWT access token ici: ").strip()
    
    if not token:
        print("\n❌ Token vide! Test annulé.")
        exit(1)
    
    # Lancer le test
    print("\n🚀 Démarrage du test...\n")
    asyncio.run(test_wss_connection(token))