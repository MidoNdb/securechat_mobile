
import 'package:chat_mobile/modules/chat/controllers/calls_controller.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

class CallsView extends GetView<CallsController> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Calls'),
      ),
      body: Center(
        child: Text('This is the Calls View'),
      ),
    );
  }
}