// // lib/core/crypto/encryption_service.dart

// import 'dart:convert';
// import 'dart:typed_data';
// import 'package:crypto/crypto.dart';
// import 'package:pointycastle/export.dart';
// import 'dart:math';

// class EncryptionService {
//   static const int PBKDF2_ITERATIONS = 100000;
//   static const int KEY_LENGTH = 32; // AES-256
//   static const int SALT_LENGTH = 32; // 256 bits
//   static const int NONCE_LENGTH = 12; // 96 bits pour GCM
  
//   /// Chiffre la clé privée avec le password utilisateur
//   static Map<String, String> encryptPrivateKey(
//     String privateKeyPem,
//     String userPassword,
//   ) {
//     try {
//       print('🔐 Début chiffrement clé privée...');
      
//       // 1. Générer un salt aléatoire
//       final random = Random.secure();
//       final salt = Uint8List.fromList(
//         List<int>.generate(SALT_LENGTH, (i) => random.nextInt(256))
//       );
      
//       print('✅ Salt généré (${salt.length} bytes)');
      
//       // 2. Dériver une clé de chiffrement avec PBKDF2
//       final key = _deriveKey(userPassword, salt);
      
//       print('✅ Clé dérivée avec PBKDF2 ($PBKDF2_ITERATIONS iterations)');
      
//       // 3. Générer nonce aléatoire
//       final nonce = Uint8List.fromList(
//         List<int>.generate(NONCE_LENGTH, (i) => random.nextInt(256))
//       );
      
//       // 4. Chiffrer avec AES-256-GCM
//       final plaintext = utf8.encode(privateKeyPem);
//       final cipher = GCMBlockCipher(AESEngine());
//       final params = AEADParameters(
//         KeyParameter(key),
//         128, // Tag length en bits
//         nonce,
//         Uint8List(0), // AAD vide
//       );
      
//       cipher.init(true, params);
      
//       final ciphertext = Uint8List(cipher.getOutputSize(plaintext.length));
//       var offset = cipher.processBytes(plaintext, 0, plaintext.length, ciphertext, 0);
//       cipher.doFinal(ciphertext, offset);
      
//       print('✅ Clé privée chiffrée avec AES-256-GCM');
      
//       // 5. Combiner nonce + ciphertext
//       final encrypted = Uint8List.fromList([...nonce, ...ciphertext]);
      
//       // 6. Encoder en base64
//       final encryptedB64 = base64.encode(encrypted);
//       final saltB64 = base64.encode(salt);
      
//       print('✅ Chiffrement terminé');
//       print('   - Taille chiffrée: ${encrypted.length} bytes');
//       print('   - Base64 length: ${encryptedB64.length}');
      
//       return {
//         'encrypted_data': encryptedB64,
//         'salt': saltB64,
//       };
      
//     } catch (e) {
//       print('❌ Erreur chiffrement: $e');
//       rethrow;
//     }
//   }
  
//   /// Déchiffre la clé privée avec le password utilisateur
//   static String decryptPrivateKey(
//     String encryptedDataB64,
//     String saltB64,
//     String userPassword,
//   ) {
//     try {
//       print('🔓 Début déchiffrement clé privée...');
      
//       // 1. Décoder depuis base64
//       final encryptedData = base64.decode(encryptedDataB64);
//       final salt = base64.decode(saltB64);
      
//       print('✅ Données décodées');
      
//       // 2. Re-dériver la même clé
//       final key = _deriveKey(userPassword, salt);
      
//       print('✅ Clé re-dérivée avec PBKDF2');
      
//       // 3. Extraire nonce et ciphertext
//       final nonce = encryptedData.sublist(0, NONCE_LENGTH);
//       final ciphertext = encryptedData.sublist(NONCE_LENGTH);
      
//       // 4. Déchiffrer avec AES-256-GCM
//       final cipher = GCMBlockCipher(AESEngine());
//       final params = AEADParameters(
//         KeyParameter(key),
//         128,
//         nonce,
//         Uint8List(0),
//       );
      
//       cipher.init(false, params);
      
//       final plaintext = Uint8List(cipher.getOutputSize(ciphertext.length));
//       var offset = cipher.processBytes(ciphertext, 0, ciphertext.length, plaintext, 0);
//       cipher.doFinal(plaintext, offset);
      
//       print('✅ Déchiffrement réussi');
      
//       // 5. Convertir en string
//       final privateKeyPem = utf8.decode(plaintext);
      
//       return privateKeyPem;
      
//     } catch (e) {
//       print('❌ Erreur déchiffrement: $e');
//       throw Exception('Impossible de déchiffrer la clé privée. Password incorrect ?');
//     }
//   }
  
//   /// Dérive une clé avec PBKDF2-SHA256
//   static Uint8List _deriveKey(String password, Uint8List salt) {
//     final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64));
//     pbkdf2.init(Pbkdf2Parameters(salt, PBKDF2_ITERATIONS, KEY_LENGTH));
    
//     final passwordBytes = utf8.encode(password);
//     return pbkdf2.process(Uint8List.fromList(passwordBytes));
//   }
// }