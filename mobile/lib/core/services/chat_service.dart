import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../api_config.dart';

class ChatHttpService {
  static final String _baseUrl = '${ApiConfig.baseUrl}/chat';

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('ev_token');
  }

  // Obtener el historial de mensajes de un incidente especifico
  static Future<List<dynamic>> obtenerHistorial(int idIncidente) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$_baseUrl/$idIncidente'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final jsonResponse = jsonDecode(response.body);
      return jsonResponse['mensajes'] ?? [];
    } else {
      throw Exception('Error al obtener el historial de chat');
    }
  }
}
