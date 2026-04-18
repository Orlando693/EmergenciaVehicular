import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../api_config.dart';

class AuthService {
  static const String _tokenKey = 'ev_token';
  static const String _userKey = 'ev_user';

  static UserModel? currentUser;

  static Future<bool> login(String email, String password) async {
    try {
      final url = Uri.parse('${ApiConfig.baseUrl}/auth/login');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final user = UserModel.fromJson(data);
        await saveSession(user);
        return true;
      } else {
        print('Error login: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Exception en login: $e');
      return false;
    }
  }

  static Future<void> saveSession(UserModel user) async {
    currentUser = user;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, user.accessToken);
    await prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  static Future<bool> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    final userJson = prefs.getString(_userKey);

    if (token != null && userJson != null) {
      final data = jsonDecode(userJson);
      currentUser = UserModel.fromJson(data);
      return true;
    }
    return false;
  }

  static Future<void> logout() async {
    currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }
}