import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../api_config.dart';

class IncidenteService {
  static final String _baseUrl = '${ApiConfig.baseUrl}/incidentes';

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('ev_token');
  }

  // Subir imagen o audio como evidencia
  static Future<String> uploadEvidence(File file) async {
    final token = await _getToken();
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/upload'),
    );
    request.headers['Authorization'] = 'Bearer $token';

    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    final response = await request.send();
    final responseData = await response.stream.bytesToString();

    if (response.statusCode == 200) {
      final jsonResponse = jsonDecode(responseData);
      return jsonResponse['url'];
    } else {
      throw Exception('Error al subir el archivo: ${response.reasonPhrase}');
    }
  }

  // Crear un nuevo incidente (con o sin GPS)
  static Future<Map<String, dynamic>> registrarIncidente({
    required int idVehiculo,
    required String descripcion,
    double? ubicacionLat,
    double? ubicacionLng,
    String? direccion,
    String? audioUrl,
    String? imagenUrl,
  }) async {
    final token = await _getToken();
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'id_vehiculo': idVehiculo,
        'descripcion': descripcion,
        // Mandamos null o 0 si no hay GPS, igual que en la web
        'ubicacion_lat': ubicacionLat ?? 0.0,
        'ubicacion_lng': ubicacionLng ?? 0.0,
        'direccion': direccion,
        'audio_url': audioUrl,
        'imagen_url': imagenUrl,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al registrar incidente: ${response.body}');
    }
  }

  // Obtener todos los incidentes (historial)
  static Future<List<dynamic>> consultarHistorial() async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse(_baseUrl),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al obtener el historial');
    }
  }

  // Obtener un incidente por ID (para ver el diagnóstico de la IA)
  static Future<Map<String, dynamic>> obtenerDetalle(int idIncidente) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$_baseUrl/$idIncidente'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al obtener los detalles del incidente');
    }
  }

  // Asignar taller automáticamente
  static Future<Map<String, dynamic>> asignarTaller(int idIncidente) async {
    final token = await _getToken();
    final response = await http.post(
      Uri.parse('$_baseUrl/$idIncidente/asignar-taller'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al asignar taller');
    }
  }
}
