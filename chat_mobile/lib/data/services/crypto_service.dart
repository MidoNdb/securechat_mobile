// lib/data/services/crypto_service.dart

import 'dart:convert';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'package:crypto/crypto.dart' hide Hmac;

/// Service centralisé pour toutes les opérations cryptographiques
/// 
/// Architecture:
/// - X25519 (Diffie-Hellman) → Secret partagé → Clé AES
/// - Ed25519 → Signatures (authenticité)
/// - AES-256-GCM → Chiffrement messages
/// - SHA-256 → Hash pour intégrité
/// - HKDF → Dérivation clé AES depuis secret DH
class CryptoService {
  // Algorithmes
  final _x25519 = X25519();
  final _ed25519 = Ed25519();
  final _aesGcm = AesGcm.with256bits();
  final _sha256 = Sha256();

  // ==================== GÉNÉRATION CLÉS ====================

  /// Génère une paire de clés DH (X25519) pour secret partagé
  Future<Map<String, String>> generateDHKeyPair() async {
    try {
      final keyPair = await _x25519.newKeyPair();
      final privateBytes = await keyPair.extractPrivateKeyBytes();
      final publicKey = await keyPair.extractPublicKey();
      
      return {
        'private': base64Encode(privateBytes),
        'public': base64Encode(publicKey.bytes),
      };
    } catch (e) {
      throw Exception('Erreur génération clé DH: $e');
    }
  }

  /// Génère une paire de clés de signature (Ed25519)
  Future<Map<String, String>> generateSignKeyPair() async {
    try {
      final keyPair = await _ed25519.newKeyPair();
      final privateBytes = await keyPair.extractPrivateKeyBytes();
      final publicKey = await keyPair.extractPublicKey();
      
      return {
        'private': base64Encode(privateBytes),
        'public': base64Encode(publicKey.bytes),
      };
    } catch (e) {
      throw Exception('Erreur génération clé signature: $e');
    }
  }

  /// Génère les 2 paires de clés (DH + Signature)
  Future<Map<String, String>> generateAllKeys() async {
    try {
      final dhKeys = await generateDHKeyPair();
      final signKeys = await generateSignKeyPair();
      
      return {
        'dh_private_key': dhKeys['private']!,
        'dh_public_key': dhKeys['public']!,
        'sign_private_key': signKeys['private']!,
        'sign_public_key': signKeys['public']!,
      };
    } catch (e) {
      throw Exception('Erreur génération clés: $e');
    }
  }

  // ==================== CALCUL SECRET PARTAGÉ ====================

  /// Calcule le secret partagé Diffie-Hellman
  /// 
  /// Alice: secret = DH(alice_private, bob_public)
  /// Bob:   secret = DH(bob_private, alice_public)
  /// → Résultat identique!
  Future<List<int>> computeSharedSecret({
    required String myDhPrivateKeyB64,
    required String theirDhPublicKeyB64,
  }) async {
    try {
      // Décoder les clés
      final myPrivateBytes = base64Decode(myDhPrivateKeyB64);
      final theirPublicBytes = base64Decode(theirDhPublicKeyB64);
      
      // Reconstituer les objets clés
      final myKeyPair = SimpleKeyPairData(
        myPrivateBytes,
        publicKey: SimplePublicKey([], type: KeyPairType.x25519),
        type: KeyPairType.x25519,
      );
      
      final theirPublicKey = SimplePublicKey(
        theirPublicBytes,
        type: KeyPairType.x25519,
      );
      
      // Calcul DH
      final sharedSecret = await _x25519.sharedSecretKey(
        keyPair: myKeyPair,
        remotePublicKey: theirPublicKey,
      );
      
      return await sharedSecret.extractBytes();
    } catch (e) {
      throw Exception('Erreur calcul secret partagé: $e');
    }
  }

  // ==================== DÉRIVATION CLÉ AES ====================

  /// Dérive une clé AES-256 depuis le secret partagé DH
  /// Utilise HKDF (HMAC-based Key Derivation Function)
  Future<List<int>> deriveAESKey(List<int> sharedSecretBytes) async {
    try {
      final hkdf = Hkdf(
        hmac: Hmac(_sha256),
        outputLength: 32, // 256 bits pour AES-256
      );
      
      final aesKeyBytes = await hkdf.deriveKey(
        secretKey: SecretKey(sharedSecretBytes),
        nonce: utf8.encode('SecureChat-v1'), // Salt
        info: utf8.encode('message-encryption'), // Context
      );
      
      return await aesKeyBytes.extractBytes();
    } catch (e) {
      throw Exception('Erreur dérivation clé AES: $e');
    }
  }

  // ==================== CHIFFREMENT MESSAGE ====================

  /// Chiffre un message avec AES-256-GCM
  /// 
  /// Étapes:
  /// 1. Calcule secret partagé DH
  /// 2. Dérive clé AES depuis secret
  /// 3. Chiffre message avec AES-GCM
  /// 4. Hash le ciphertext (intégrité)
  /// 5. Signe le hash (authenticité)
  /// 
  /// Retourne: {ciphertext, nonce, auth_tag, signature}
  Future<Map<String, String>> encryptMessage({
    required String plaintext,
    required String myDhPrivateKeyB64,
    required String theirDhPublicKeyB64,
    required String mySignPrivateKeyB64,
  }) async {
    try {
      print('🔐 Chiffrement message...');
      
      // 1. Calculer secret partagé DH
      final sharedSecretBytes = await computeSharedSecret(
        myDhPrivateKeyB64: myDhPrivateKeyB64,
        theirDhPublicKeyB64: theirDhPublicKeyB64,
      );
      
      print('✅ Secret partagé calculé (${sharedSecretBytes.length} bytes)');
      
      // 2. Dériver clé AES
      final aesKeyBytes = await deriveAESKey(sharedSecretBytes);
      print('✅ Clé AES dérivée (${aesKeyBytes.length} bytes)');
      
      // 3. Chiffrer avec AES-256-GCM
      final secretBox = await _aesGcm.encrypt(
        utf8.encode(plaintext),
        secretKey: SecretKey(aesKeyBytes),
      );
      
      print('✅ Message chiffré');
      
      // 4. Hash du ciphertext (intégrité)
      final ciphertextHash = await _sha256.hash(secretBox.cipherText);
      print('✅ Hash calculé');
      
      // 5. Signer avec Ed25519 (authenticité)
      final signature = await _signData(
        ciphertextHash.bytes,
        mySignPrivateKeyB64,
      );
      
      print('✅ Signature créée');
      
      return {
        'ciphertext': base64Encode(secretBox.cipherText),
        'nonce': base64Encode(secretBox.nonce),
        'auth_tag': base64Encode(secretBox.mac.bytes),
        'signature': signature,
      };
    } catch (e) {
      throw Exception('Erreur chiffrement: $e');
    }
  }

  // ==================== DÉCHIFFREMENT MESSAGE ====================

  /// Déchiffre un message
  /// 
  /// Étapes:
  /// 1. Vérifie la signature (authenticité)
  /// 2. Recalcule secret partagé DH
  /// 3. Dérive clé AES
  /// 4. Déchiffre avec AES-GCM
  Future<String> decryptMessage({
    required String ciphertextB64,
    required String nonceB64,
    required String authTagB64,
    required String signatureB64,
    required String myDhPrivateKeyB64,
    required String theirDhPublicKeyB64,
    required String theirSignPublicKeyB64,
  }) async {
    try {
      print('🔓 Déchiffrement message...');
      
      // 1. Décoder
      final ciphertext = base64Decode(ciphertextB64);
      final nonce = base64Decode(nonceB64);
      final authTag = base64Decode(authTagB64);
      
      // 2. Vérifier signature AVANT de déchiffrer
      final ciphertextHash = await _sha256.hash(ciphertext);
      
      final isValidSignature = await _verifySignature(
        ciphertextHash.bytes,
        signatureB64,
        theirSignPublicKeyB64,
      );
      
      if (!isValidSignature) {
        throw Exception('❌ Signature invalide - Message compromis!');
      }
      
      print('✅ Signature valide');
      
      // 3. Calculer secret partagé DH
      final sharedSecretBytes = await computeSharedSecret(
        myDhPrivateKeyB64: myDhPrivateKeyB64,
        theirDhPublicKeyB64: theirDhPublicKeyB64,
      );
      
      // 4. Dériver clé AES
      final aesKeyBytes = await deriveAESKey(sharedSecretBytes);
      
      // 5. Déchiffrer
      final secretBox = SecretBox(
        ciphertext,
        nonce: nonce,
        mac: Mac(authTag),
      );
      
      final decryptedBytes = await _aesGcm.decrypt(
        secretBox,
        secretKey: SecretKey(aesKeyBytes),
      );
      
      print('✅ Message déchiffré');
      
      return utf8.decode(decryptedBytes);
    } catch (e) {
      throw Exception('Erreur déchiffrement: $e');
    }
  }

  // ==================== SIGNATURE / VÉRIFICATION ====================

  /// Signe des données avec Ed25519
  Future<String> _signData(
    List<int> data,
    String signPrivateKeyB64,
  ) async {
    try {
      final privateBytes = base64Decode(signPrivateKeyB64);
      
      final keyPair = SimpleKeyPairData(
        privateBytes,
        publicKey: SimplePublicKey([], type: KeyPairType.ed25519),
        type: KeyPairType.ed25519,
      );
      
      final signature = await _ed25519.sign(
        data,
        keyPair: keyPair,
      );
      
      return base64Encode(signature.bytes);
    } catch (e) {
      throw Exception('Erreur signature: $e');
    }
  }

  /// Vérifie une signature Ed25519
  Future<bool> _verifySignature(
    List<int> data,
    String signatureB64,
    String signPublicKeyB64,
  ) async {
    try {
      final signatureBytes = base64Decode(signatureB64);
      final publicKeyBytes = base64Decode(signPublicKeyB64);
      
      final publicKey = SimplePublicKey(
        publicKeyBytes,
        type: KeyPairType.ed25519,
      );
      
      final signature = Signature(
        signatureBytes,
        publicKey: publicKey,
      );
      
      return await _ed25519.verify(
        data,
        signature: signature,
      );
    } catch (e) {
      print('❌ Erreur vérification signature: $e');
      return false;
    }
  }

  // ==================== HASH ====================

  /// Calcule SHA-256 d'une chaîne
  String hashString(String input) {
    final bytes = utf8.encode(input);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Calcule SHA-256 de bytes
  Future<List<int>> hashBytes(List<int> input) async {
    final hash = await _sha256.hash(input);
    return hash.bytes;
  }
}