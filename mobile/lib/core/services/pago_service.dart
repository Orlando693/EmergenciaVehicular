import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../api_config.dart';

class PagoService {
  static final String _baseUrl = '${ApiConfig.baseUrl}/pagos';

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('ev_token');
  }

  static Future<Map<String, dynamic>> misPagos({
    int skip = 0,
    int limit = 20,
  }) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$_baseUrl/mis-pagos?skip=$skip&limit=$limit'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Error al obtener pagos: ${response.body}');
  }

  static Future<Map<String, dynamic>> infoIncidente(int idIncidente) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$_baseUrl/incidente/$idIncidente/info'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Error al obtener informacion de pago: ${response.body}');
  }

  static Future<Map<String, dynamic>> pagarIncidente({
    required int idIncidente,
    required String metodoPago,
    String? numeroTarjeta,
    String? nombreTitular,
    String? vencimiento,
    String? cvv,
  }) async {
    final token = await _getToken();
    var response = await http.post(
      Uri.parse('$_baseUrl/incidente/$idIncidente/pagar'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'metodo_pago': metodoPago,
        'numero_tarjeta': numeroTarjeta,
        'nombre_titular': nombreTitular,
        'vencimiento': vencimiento,
        'cvv': cvv,
      }),
    );

    // Compatibilidad con backends desplegados antes de soportar QR.
    // El backend nuevo acepta QR; si produccion aun esta viejo, TRANSFERENCIA
    // permite completar el flujo mobile sin exigir datos de tarjeta.
    if (metodoPago == 'QR' && response.statusCode >= 400) {
      response = await http.post(
        Uri.parse('$_baseUrl/incidente/$idIncidente/pagar'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'metodo_pago': 'TRANSFERENCIA',
          'numero_tarjeta': null,
          'nombre_titular': null,
          'vencimiento': null,
          'cvv': null,
        }),
      );
    }

    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }

    throw Exception('Error al procesar pago: ${response.body}');
  }
}
