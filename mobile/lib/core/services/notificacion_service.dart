import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../api_config.dart';

class NotificacionService {
  static final String _baseUrl = '${ApiConfig.baseUrl}/notificaciones';

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('ev_token');
  }

  static Future<Map<String, dynamic>> listar({
    int skip = 0,
    int limit = 20,
  }) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$_baseUrl?skip=$skip&limit=$limit'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Error al obtener notificaciones: ${response.body}');
  }

  static Future<void> marcarLeida(int idNotificacion) async {
    final token = await _getToken();
    final response = await http.patch(
      Uri.parse('$_baseUrl/$idNotificacion/leer'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Error al marcar notificacion: ${response.body}');
    }
  }

  static Future<void> marcarTodasLeidas() async {
    final token = await _getToken();
    final response = await http.patch(
      Uri.parse('$_baseUrl/leer-todas'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Error al marcar notificaciones: ${response.body}');
    }
  }
}
