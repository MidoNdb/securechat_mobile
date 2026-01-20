// lib/modules/chat/widgets/search_bar_widget.dart

import 'package:flutter/material.dart';

class SearchBarWidget extends StatefulWidget {
  final ValueChanged<String> onChanged;
  final String hintText;

  const SearchBarWidget({
    Key? key,
    required this.onChanged,
    this.hintText = 'Rechercher une conversation...',
  }) : super(key: key);

  @override
  State<SearchBarWidget> createState() => _SearchBarWidgetState();
}

class _SearchBarWidgetState extends State<SearchBarWidget> {
  late final TextEditingController _controller;
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    
    // ✅ Écouter les changements pour afficher/masquer l'icône X
    _controller.addListener(_onTextChanged);
  }

  void _onTextChanged() {
    final hasText = _controller.text.isNotEmpty;
    
    // ✅ Mettre à jour l'état seulement si ça change
    if (hasText != _hasText) {
      setState(() {
        _hasText = hasText;
      });
    }
    
    // ✅ Notifier le parent
    widget.onChanged(_controller.text);
  }

  void _clearText() {
    _controller.clear();
    // onChanged sera appelé automatiquement via le listener
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: TextField(
        controller: _controller,
        style: const TextStyle(
          color: Colors.black87,
          fontSize: 15,
        ),
        decoration: InputDecoration(
          hintText: widget.hintText,
          hintStyle: TextStyle(
            color: Colors.grey[500],
            fontSize: 15,
          ),
          prefixIcon: Icon(
            Icons.search,
            color: Colors.grey[600],
          ),
          // ✅ Afficher l'icône X seulement s'il y a du texte
          suffixIcon: _hasText
              ? IconButton(
                  icon: Icon(
                    Icons.clear,
                    color: Colors.grey[600],
                  ),
                  onPressed: _clearText,
                )
              : null,
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 14,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(25),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(25),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(25),
            borderSide: const BorderSide(
              color: Color(0xFF667eea),
              width: 2,
            ),
          ),
        ),
      ),
    );
  }
}



// // lib/modules/chat/widgets/search_bar_widget.dart

// import 'package:flutter/material.dart';
// import 'dart:async';

// class SearchBarWidget extends StatefulWidget {
//   final Function(String) onChanged;
//   final String? hintText;

//   const SearchBarWidget({
//     Key? key,
//     required this.onChanged,
//     this.hintText,
//   }) : super(key: key);

//   @override
//   State<SearchBarWidget> createState() => _SearchBarWidgetState();
// }

// class _SearchBarWidgetState extends State<SearchBarWidget> {
//   final TextEditingController _controller = TextEditingController();
//   Timer? _debounce;

//   @override
//   void dispose() {
//     _controller.dispose();
//     _debounce?.cancel();
//     super.dispose();
//   }

//   void _onSearchChanged(String query) {
//     if (_debounce?.isActive ?? false) _debounce!.cancel();
//     _debounce = Timer(const Duration(milliseconds: 300), () {
//       widget.onChanged(query);
//     });
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Container(
//       decoration: BoxDecoration(
//         color: Colors.white.withOpacity(0.25),
//         borderRadius: BorderRadius.circular(12),
//         border: Border.all(
//           color: Colors.white.withOpacity(0.2),
//           width: 1,
//         ),
//       ),
//       child: TextField(
//         controller: _controller,
//         onChanged: _onSearchChanged,
//         style: TextStyle(color: Colors.white, fontSize: 15),
//         decoration: InputDecoration(
//           hintText: widget.hintText ?? 'Rechercher une conversation...',
//           hintStyle: TextStyle(
//             color: Colors.white.withOpacity(0.9),
//             fontSize: 15,
//           ),
//           prefixIcon: Icon(
//             Icons.search,
//             color: Colors.white,
//             size: 20,
//           ),
//           suffixIcon: _controller.text.isNotEmpty
//               ? IconButton(
//                   icon: Icon(
//                     Icons.clear,
//                     color: Colors.white,
//                     size: 20,
//                   ),
//                   onPressed: () {
//                     _controller.clear();
//                     widget.onChanged('');
//                   },
//                 )
//               : null,
//           border: InputBorder.none,
//           contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
//         ),
//       ),
//     );
//   }
// }