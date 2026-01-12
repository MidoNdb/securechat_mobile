// lib/modules/chat/controllers/contacts_controller.dart

import 'package:chat_mobile/modules/chat/controllers/messages_controller.dart';
import 'package:get/get.dart';
import 'package:flutter/material.dart';
import '../../../data/services/contact_service.dart';
import '../../../data/models/contact.dart' as models;

class ContactsController extends GetxController {
  final ContactService _contactService = Get.find<ContactService>();

  final contacts = <Map<String, dynamic>>[].obs;
  final isLoading = false.obs;
  final searchQuery = ''.obs;

  @override
  void onInit() {
    super.onInit();
    loadContacts();
  }

  Future<void> loadContacts() async {
    try {
      isLoading.value = true;
      final result = await _contactService.getContacts();
      contacts.assignAll(result);
    } finally {
      isLoading.value = false;
    }
  }

  Future<Map<String, dynamic>?> checkPhoneExists(String phoneNumber) async {
    return await _contactService.checkPhoneNumber(phoneNumber);
  }

 // lib/modules/chat/controllers/contacts_controller.dart

Future<bool> addContact({
  required String phoneNumber,
  required String nickname,
  String? notes,
}) async {
  try {
    isLoading.value = true;

    print('🔄 ContactsController.addContact:');
    print('   Phone: $phoneNumber');
    print('   Nickname: "$nickname"');

    final newContact = await _contactService.addContact(
      phoneNumber: phoneNumber,
      nickname: nickname,
      notes: notes,
    );

    if (newContact != null) {
      print('Contact received from service:');
      print('   ID: ${newContact['id']}');
      print('   Display name: ${newContact['display_name']}');
      print('   Nickname: ${newContact['nickname']}');
      
      contacts.insert(0, newContact);
      
      Get.snackbar(
        'Succès',
        'Contact "${newContact['display_name']}" ajouté',  // ✅ Affiche le nom
        backgroundColor: Colors.green.withOpacity(0.1),
        colorText: Colors.green,
        duration: const Duration(seconds: 2),
      );
      
      return true;  // ✅ IMPORTANT: Retourne true
    }

    print('newContact is null');
    return false;
  } catch (e) {
    print('addContact exception: $e');
    Get.snackbar(
      'Erreur',
      e.toString().contains('already exists')
          ? 'Ce contact existe déjà'
          : 'Impossible d\'ajouter le contact',
      backgroundColor: Colors.red.withOpacity(0.1),
      colorText: Colors.red,
      duration: const Duration(seconds: 3),
    );
    return false;
  } finally {
    isLoading.value = false;
  }
}

  Future<void> toggleBlock(String contactId, bool currentlyBlocked) async {
    final success = await _contactService.toggleBlock(contactId, currentlyBlocked);
    
    if (success) {
      final index = contacts.indexWhere((c) => c['id'] == contactId);
      if (index != -1) {
        contacts[index]['is_blocked'] = !currentlyBlocked;
        contacts.refresh();
      }
      
      Get.snackbar(
        '',
        currentlyBlocked ? 'Contact débloqué' : 'Contact bloqué',
        backgroundColor: Colors.green.withOpacity(0.1),
        colorText: Colors.green,
      );
    }
  }

  Future<void> toggleFavorite(String contactId, bool currentlyFavorite) async {
    final success = await _contactService.toggleFavorite(contactId);
    
    if (success) {
      final index = contacts.indexWhere((c) => c['id'] == contactId);
      if (index != -1) {
        contacts[index]['is_favorite'] = !currentlyFavorite;
        contacts.refresh();
      }
    }
  }

  Future<void> deleteContact(String contactId) async {
    final confirmed = await Get.dialog<bool>(
      AlertDialog(
        title: const Text('Confirmer'),
        content: const Text('Supprimer ce contact ?'),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () => Get.back(result: true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await _contactService.deleteContact(contactId);
      
      if (success) {
        contacts.removeWhere((c) => c['id'] == contactId);
        Get.snackbar(
          '✅',
          'Contact supprimé',
          backgroundColor: Colors.green.withOpacity(0.1),
          colorText: Colors.green,
        );
      }
    }
  }

  void searchContacts(String query) {
    searchQuery.value = query;
  }

  List<Map<String, dynamic>> get filteredContacts {
    if (searchQuery.isEmpty) return contacts;

    return contacts.where((contact) {
      final name = (contact['display_name'] ?? '').toString().toLowerCase();
      final phone = (contact['contact_phone'] ?? '').toString();
      final query = searchQuery.value.toLowerCase();

      return name.contains(query) || phone.contains(query);
    }).toList();
  }

  List<Map<String, dynamic>> get favoriteContacts {
    return contacts.where((c) => c['is_favorite'] == true).toList();
  }

  List<Map<String, dynamic>> get blockedContacts {
    return contacts.where((c) => c['is_blocked'] == true).toList();
  }

  // lib/modules/chat/controllers/contacts_controller.dart

// ✅ Quand un contact est sélectionné
void onContactTap(Map<String, dynamic> contact) {
  final contactUserId = contact['contact_user_id']?.toString();
  final contactName = contact['display_name'] ?? 'Contact';
  
  if (contactUserId == null) {
    Get.snackbar('❌', 'ID utilisateur manquant');
    return;
  }
  
  print('📞 Contact selected: $contactName ($contactUserId)');
  
  // ✅ Appelle MessagesController pour gérer la navigation
  final messagesController = Get.find<MessagesController>();
  messagesController.openOrCreateConversation(
    contactUserId: contactUserId,
    contactName: contactName,
  );
}
}



// // lib/modules/chat/controllers/contacts_controller.dart
// import 'package:get/get.dart';
// import 'package:dio/dio.dart';
// import 'package:flutter/material.dart';
// import 'package:chat_mobile/data/api/dio_client.dart';

// class ContactsController extends GetxController {
//   late final DioClient _dioClient;

//   var contacts = <Map<String, dynamic>>[].obs;
//   var isLoading = false.obs;
//   var error = Rx<String?>(null);

//   @override
//   void onInit() {
//     super.onInit();
//     _dioClient = Get.find<DioClient>();
    
//     Future.delayed(const Duration(milliseconds: 500), () {
//       loadContacts();
//     });
//   }

//   // ========================================
//   // 1. Get all contacts
//   // ========================================
  
//   Future<void> loadContacts({
//     bool? favorites,
//     bool? blocked,
//     String? search,
//   }) async {
//     try {
//       isLoading.value = true;
//       error.value = null;
      
//       print('🔄 Loading contacts...');
      
//       Map<String, dynamic> params = {};
//       if (favorites != null) params['favorites'] = favorites.toString();
//       if (blocked != null) params['blocked'] = blocked.toString();
//       if (search != null && search.isNotEmpty) params['search'] = search;
      
//       final response = await _dioClient.get(
//         '/contact/',
//         queryParameters: params,
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true && data['data'] is List) {
//           contacts.value = (data['data'] as List)
//               .map((item) => item as Map<String, dynamic>)
//               .toList();
          
//           print('✅ Loaded ${contacts.length} contacts');
//         } else if (data is List) {
//           contacts.value = data
//               .map((item) => item as Map<String, dynamic>)
//               .toList();
          
//           print('✅ Loaded ${contacts.length} contacts');
//         } else {
//           print('⚠️ Unexpected response structure');
//           contacts.value = [];
//         }
//       }
      
//     } on DioException catch (e) {
//       error.value = _handleError(e);
//       print('❌ Error loading contacts: ${error.value}');
      
//       Get.snackbar(
//         'Error',
//         error.value ?? 'Failed to load contacts',
//         snackPosition: SnackPosition.BOTTOM,
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//     } catch (e) {
//       error.value = e.toString();
//       print('❌ Unexpected error: $e');
//     } finally {
//       isLoading.value = false;
//     }
//   }

//   // ========================================
//   // 2. Add contact by phone number
//   // ========================================
  
//   Future<bool> addContactByPhone({
//     required String phoneNumber,
//     String? displayName,
//     String? notes,
//   }) async {
//     try {
//       isLoading.value = true;
      
//       print('🔄 Adding contact...');
//       print('   📱 Phone: $phoneNumber');
//       print('   👤 Name: $displayName');
      
//       // ✅ CORRECTION: Ajout de data: {}
//       final response = await _dioClient.post(
//         '/contact/',
//         data: {
//           'phone_number': phoneNumber,
//           'display_name': displayName ?? '',
//           'notes': notes ?? '',
//         },
//       );

//       if (response.statusCode == 201 || response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true && data['data'] != null) {
//           contacts.add(data['data'] as Map<String, dynamic>);
          
//           print('✅ Contact added successfully');
          
//           Get.snackbar(
//             '✅ Success',
//             data['message'] ?? 'Contact added successfully',
//             snackPosition: SnackPosition.BOTTOM,
//             backgroundColor: Colors.green,
//             colorText: Colors.white,
//           );
          
//           return true;
//         }
//       }
      
//       return false;
//     } on DioException catch (e) {
//       error.value = _handleError(e);
//       print('❌ Error adding contact: ${error.value}');
      
//       Get.snackbar(
//         '❌ Error',
//         error.value ?? 'Failed to add contact',
//         snackPosition: SnackPosition.BOTTOM,
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//       return false;
//     } finally {
//       isLoading.value = false;
//     }
//   }

//   // ========================================
//   // 3. Update contact
//   // ========================================
  
//   Future<bool> updateContact({
//     required int contactId,
//     String? displayName,
//     bool? isBlocked,
//     bool? isFavorite,
//     String? notes,
//   }) async {
//     try {
//       print('🔄 Updating contact...');
      
//       Map<String, dynamic> data = {};
//       if (displayName != null) data['display_name'] = displayName;
//       if (isBlocked != null) data['is_blocked'] = isBlocked;
//       if (isFavorite != null) data['is_favorite'] = isFavorite;
//       if (notes != null) data['notes'] = notes;

//       final response = await _dioClient.patch(
//         '/contact/$contactId/',
//         data: data,
//       );

//       if (response.statusCode == 200) {
//         final responseData = response.data;
        
//         if (responseData is Map && responseData['success'] == true) {
//           final index = contacts.indexWhere((c) => c['id'] == contactId);
//           if (index != -1) {
//             contacts[index] = responseData['data'] as Map<String, dynamic>;
//             contacts.refresh();
//           }
          
//           print('✅ Updated successfully');
//           Get.snackbar(
//             '✅ Success', 
//             'Contact updated successfully',
//             backgroundColor: Colors.green,
//             colorText: Colors.white,
//           );
//           return true;
//         }
//       }
      
//       return false;
//     } on DioException catch (e) {
//       error.value = _handleError(e);
//       print('❌ Update error: ${error.value}');
//       Get.snackbar(
//         '❌ Error', 
//         error.value ?? 'Failed to update',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//       return false;
//     }
//   }

//   // ========================================
//   // 4. Delete contact
//   // ========================================
  
//   Future<bool> deleteContact(int contactId) async {
//     try {
//       print('🔄 Deleting contact...');
      
//       final response = await _dioClient.delete('/contact/$contactId/');

//       if (response.statusCode == 200 || response.statusCode == 204) {
//         contacts.removeWhere((c) => c['id'] == contactId);
        
//         print('✅ Deleted successfully');
//         Get.snackbar(
//           '✅ Success', 
//           'Contact deleted successfully',
//           backgroundColor: Colors.green,
//           colorText: Colors.white,
//         );
//         return true;
//       }
      
//       return false;
//     } on DioException catch (e) {
//       error.value = _handleError(e);
//       print('❌ Delete error: ${error.value}');
//       Get.snackbar(
//         '❌ Error', 
//         error.value ?? 'Failed to delete',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//       return false;
//     }
//   }

//   // ========================================
//   // 5. Block contact - ✅ CORRIGÉ
//   // ========================================
  
//   Future<void> blockContact(int contactId) async {
//     try {
//       print('🔄 Blocking contact...');
      
//       // ✅ CORRECTION: Ajout de data: {}
//       final response = await _dioClient.post(
//         '/contact/$contactId/block/',
//         data: {},
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true) {
//           final index = contacts.indexWhere((c) => c['id'] == contactId);
//           if (index != -1) {
//             contacts[index] = data['data'] as Map<String, dynamic>;
//             contacts.refresh();
//           }
          
//           print('✅ Contact blocked');
//           Get.snackbar(
//             '✅ Blocked', 
//             'Contact has been blocked',
//             backgroundColor: Colors.orange,
//             colorText: Colors.white,
//           );
//         }
//       }
//     } on DioException catch (e) {
//       print('❌ Block error: ${_handleError(e)}');
//       Get.snackbar(
//         '❌ Error', 
//         'Failed to block contact',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//     }
//   }

//   // ========================================
//   // 6. Unblock contact
//   // ========================================
  
//   Future<void> unblockContact(int contactId) async {
//     try {
//       print('🔄 Unblocking contact...');
      
//       final response = await _dioClient.delete('/contact/$contactId/block/');
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true) {
//           final index = contacts.indexWhere((c) => c['id'] == contactId);
//           if (index != -1) {
//             contacts[index] = data['data'] as Map<String, dynamic>;
//             contacts.refresh();
//           }
          
//           print('✅ Contact unblocked');
//           Get.snackbar(
//             '✅ Unblocked', 
//             'Contact has been unblocked',
//             backgroundColor: Colors.green,
//             colorText: Colors.white,
//           );
//         }
//       }
//     } on DioException catch (e) {
//       print('❌ Error: ${_handleError(e)}');
//       Get.snackbar(
//         '❌ Error', 
//         'Failed to unblock contact',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//     }
//   }

//   // ========================================
//   // 7. Add to favorites - ✅ CORRIGÉ
//   // ========================================
  
//   Future<void> addToFavorites(int contactId) async {
//     try {
//       print('🔄 Adding to favorites...');
      
//       // ✅ CORRECTION: Ajout de data: {}
//       final response = await _dioClient.post(
//         '/contact/$contactId/favorite/',
//         data: {},
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true) {
//           final index = contacts.indexWhere((c) => c['id'] == contactId);
//           if (index != -1) {
//             contacts[index] = data['data'] as Map<String, dynamic>;
//             contacts.refresh();
//           }
          
//           print('✅ Added to favorites');
//           Get.snackbar(
//             '✅ Favorite', 
//             'Added to favorites',
//             backgroundColor: Colors.amber,
//             colorText: Colors.white,
//           );
//         }
//       }
//     } on DioException catch (e) {
//       print('❌ Error: ${_handleError(e)}');
//       Get.snackbar(
//         '❌ Error', 
//         'Failed to add to favorites',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//     }
//   }

//   // ========================================
//   // 8. Remove from favorites
//   // ========================================
  
//   Future<void> removeFromFavorites(int contactId) async {
//     try {
//       print('🔄 Removing from favorites...');
      
//       final response = await _dioClient.delete('/contact/$contactId/favorite/');
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true) {
//           final index = contacts.indexWhere((c) => c['id'] == contactId);
//           if (index != -1) {
//             contacts[index] = data['data'] as Map<String, dynamic>;
//             contacts.refresh();
//           }
          
//           print('✅ Removed from favorites');
//           Get.snackbar(
//             '✅ Removed', 
//             'Removed from favorites',
//             backgroundColor: Colors.grey,
//             colorText: Colors.white,
//           );
//         }
//       }
//     } on DioException catch (e) {
//       print('❌ Error: ${_handleError(e)}');
//       Get.snackbar(
//         '❌ Error', 
//         'Failed to remove from favorites',
//         backgroundColor: Colors.red,
//         colorText: Colors.white,
//       );
//     }
//   }

//   // ========================================
//   // 9. Search contacts
//   // ========================================
  
//   Future<List<Map<String, dynamic>>> searchContacts(String query) async {
//     if (query.isEmpty) return contacts;
    
//     try {
//       final response = await _dioClient.get(
//         '/contact/search/',
//         queryParameters: {'q': query},
//       );
      
//       if (response.statusCode == 200) {
//         final data = response.data;
        
//         if (data is Map && data['success'] == true && data['data'] is List) {
//           return (data['data'] as List)
//               .map((item) => item as Map<String, dynamic>)
//               .toList();
//         } else if (data is List) {
//           return data
//               .map((item) => item as Map<String, dynamic>)
//               .toList();
//         }
//       }
//     } on DioException catch (e) {
//       print('❌ Search error: ${_handleError(e)}');
//     }
    
//     return [];
//   }

//   // ========================================
//   // 10. Toggle favorite
//   // ========================================
  
//   Future<void> toggleFavorite(int contactId) async {
//     final contact = contacts.firstWhereOrNull((c) => c['id'] == contactId);
//     if (contact == null) return;
    
//     final isFavorite = contact['is_favorite'] ?? false;
    
//     if (isFavorite) {
//       await removeFromFavorites(contactId);
//     } else {
//       await addToFavorites(contactId);
//     }
//   }

//   // ========================================
//   // 11. Toggle block
//   // ========================================
  
//   Future<void> toggleBlock(int contactId) async {
//     final contact = contacts.firstWhereOrNull((c) => c['id'] == contactId);
//     if (contact == null) return;
    
//     final isBlocked = contact['is_blocked'] ?? false;
    
//     if (isBlocked) {
//       await unblockContact(contactId);
//     } else {
//       await blockContact(contactId);
//     }
//   }

//   // ========================================
//   // Error handling
//   // ========================================
  
//   String _handleError(DioException error) {
//     if (error.response?.data != null && error.response?.data is Map) {
//       final data = error.response!.data as Map;
      
//       if (data['error'] != null && data['error']['message'] != null) {
//         return data['error']['message'];
//       }
      
//       if (data['detail'] != null) {
//         return data['detail'];
//       }
//     }
    
//     switch (error.type) {
//       case DioExceptionType.connectionTimeout:
//         return 'Connection timeout - Check your internet';
//       case DioExceptionType.sendTimeout:
//         return 'Send timeout';
//       case DioExceptionType.receiveTimeout:
//         return 'Receive timeout';
//       case DioExceptionType.badResponse:
//         final statusCode = error.response?.statusCode;
//         if (statusCode == 404) return 'Contact not found';
//         if (statusCode == 400) return 'Invalid data';
//         if (statusCode == 401) return 'Unauthorized - Please login';
//         if (statusCode == 409) return 'Contact already exists';
//         if (statusCode == 500) return 'Server error';
//         return 'Server error: $statusCode';
//       case DioExceptionType.cancel:
//         return 'Request cancelled';
//       case DioExceptionType.connectionError:
//         return 'No connection - Make sure Django is running on http://127.0.0.1:8000';
//       default:
//         return 'Unexpected error: ${error.message}';
//     }
//   }

//   // ========================================
//   // Filtered lists getters
//   // ========================================
  
//   List<Map<String, dynamic>> get favoriteContacts => 
//       contacts.where((c) => c['is_favorite'] == true).toList();

//   List<Map<String, dynamic>> get blockedContacts => 
//       contacts.where((c) => c['is_blocked'] == true).toList();

//   List<Map<String, dynamic>> get activeContacts => 
//       contacts.where((c) => c['is_blocked'] != true).toList();
// }