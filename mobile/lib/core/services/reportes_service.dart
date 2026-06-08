import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../api_config.dart';
import 'auth_service.dart';

class ReportesService {
  static final String _baseUrl = '${ApiConfig.baseUrl}/reportes';

  static Map<String, String> get _jsonHeaders => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${AuthService.currentUser?.accessToken ?? ''}',
      };

  static Future<Map<String, dynamic>> resumen() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/resumen'),
      headers: _jsonHeaders,
    );
    return _decodeMap(response, 'No se pudo cargar el resumen');
  }

  static Future<Map<String, dynamic>> incidentes() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/incidentes'),
      headers: _jsonHeaders,
    );
    return _decodeMap(response, 'No se pudo cargar reporte de incidentes');
  }

  static Future<Map<String, dynamic>> pagos() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/pagos'),
      headers: _jsonHeaders,
    );
    return _decodeMap(response, 'No se pudo cargar reporte de pagos');
  }

  static Future<Map<String, dynamic>> usuarios() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/usuarios'),
      headers: _jsonHeaders,
    );
    return _decodeMap(response, 'No se pudo cargar reporte de usuarios');
  }

  static Future<Map<String, dynamic>> talleres() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/talleres'),
      headers: _jsonHeaders,
    );
    return _decodeMap(response, 'No se pudo cargar reporte de talleres');
  }

  static Future<Map<String, dynamic>> subirAudio(File file) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/audio'),
    );
    request.headers['Authorization'] =
        'Bearer ${AuthService.currentUser?.accessToken ?? ''}';
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    final streamed = await request.send();
    final body = await streamed.stream.bytesToString();
    final response = http.Response(body, streamed.statusCode);
    return _decodeMap(response, 'No se pudo enviar el audio');
  }

  static Map<String, dynamic> _decodeMap(http.Response response, String error) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('$error: ${response.body}');
  }
}
