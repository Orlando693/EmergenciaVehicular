import 'dart:convert';
import 'package:http/http.dart' as http;
import '../api_config.dart';
import 'auth_service.dart';

class UsuarioService {
  static Future<List<dynamic>> listarUsuarios() async {
    if (AuthService.currentUser == null) return [];

    try {
      final url = Uri.parse('${ApiConfig.baseUrl}/usuarios');
      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${AuthService.currentUser!.accessToken}'
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      } else {
        print('Error listarUsuarios: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('Excepción listarUsuarios: $e');
      return [];
    }
  }

  static Future<Map<String, dynamic>?> miPerfil() async {
    if (AuthService.currentUser == null) return null;

    try {
      final url = Uri.parse('${ApiConfig.baseUrl}/usuarios/me');
      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${AuthService.currentUser!.accessToken}'
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print('Error miPerfil: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Excepción miPerfil: $e');
      return null;
    }
  }
}
