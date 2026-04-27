import 'dart:async';
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../api_config.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final _streamController = StreamController<dynamic>.broadcast();

  // Para escuchar los mensajes/notificaciones en cualquier pantalla
  Stream<dynamic> get stream => _streamController.stream;

  Future<void> connect(String endpoint) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('ev_token');

      if (token == null) return;

      // Transformar HTTP a WS
      final wsUrl = ApiConfig.baseUrl.replaceFirst('http', 'ws');
      final uri = Uri.parse('$wsUrl$endpoint?token=$token');

      _channel = WebSocketChannel.connect(uri);

      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          _streamController.add(data);
        },
        onError: (error) {
          print('WebSocket Error: $error');
        },
        onDone: () {
          print('WebSocket Desconectado');
        },
      );
    } catch (e) {
      print('Error conectando a WebSocket: $e');
    }
  }

  void sendMessage(Map<String, dynamic> data) {
    if (_channel != null) {
      _channel!.sink.add(jsonEncode(data));
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }
}
