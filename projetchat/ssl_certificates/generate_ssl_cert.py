#!/usr/bin/env python
"""
═══════════════════════════════════════════════════════════════
Générateur de certificat SSL auto-signé pour Windows
═══════════════════════════════════════════════════════════════
Utilise la bibliothèque cryptography (pure Python)
"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import os

def generate_self_signed_cert():
    """Générer un certificat SSL auto-signé"""
    
    print("═══════════════════════════════════════════════════════════")
    print("🔒 Génération du certificat SSL auto-signé")
    print("═══════════════════════════════════════════════════════════")
    
    # Générer la clé privée RSA
    print("🔑 Génération de la clé privée RSA 4096 bits...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )
    print("   ✅ Clé privée générée")
    
    # Informations du certificat
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "France"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DevLocal"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    # Créer le certificat
    print("📄 Création du certificat X.509...")
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        # Valide pour 1 an
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    print("   ✅ Certificat créé")
    
    # Sauvegarder la clé privée
    key_path = "key.pem"
    print(f"💾 Sauvegarde de la clé privée: {key_path}")
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print("   ✅ Clé privée sauvegardée")
    
    # Sauvegarder le certificat
    cert_path = "cert.pem"
    print(f"💾 Sauvegarde du certificat: {cert_path}")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print("   ✅ Certificat sauvegardé")
    
    print("\n═══════════════════════════════════════════════════════════")
    print("✅ Certificats SSL générés avec succès!")
    print("═══════════════════════════════════════════════════════════")
    print(f"📁 Clé privée:  {os.path.abspath(key_path)}")
    print(f"📁 Certificat:  {os.path.abspath(cert_path)}")
    print(f"📅 Validité:    365 jours")
    print("═══════════════════════════════════════════════════════════")
    print("\n🚀 Vous pouvez maintenant lancer:")
    print("   python run_wss_server.py")
    print("═══════════════════════════════════════════════════════════")

if __name__ == "__main__":
    try:
        import ipaddress
        generate_self_signed_cert()
    except ImportError:
        print("❌ ERREUR: La bibliothèque 'cryptography' n'est pas installée")
        print("\n📦 Installation:")
        print("   pip install cryptography")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)