import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../api_config.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class PushNotificationService {
  static const _channel = AndroidNotificationChannel(
    'emergencia_high_importance',
    'Emergencia Vehicular',
    description: 'Alertas importantes de incidentes y servicios.',
    importance: Importance.max,
  );

  static final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;

    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

      await _setupLocalNotifications();
      await _requestPermission();
      await registrarTokenActual();

      FirebaseMessaging.instance.onTokenRefresh.listen((token) {
        registrarToken(token);
      });

      FirebaseMessaging.onMessage.listen(_showForegroundNotification);
      _initialized = true;
    } catch (e) {
      print('Push Firebase no inicializado: $e');
    }
  }

  static Future<void> _setupLocalNotifications() async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);
    await _localNotifications.initialize(settings: initSettings);

    await _localNotifications
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(_channel);
  }

  static Future<void> _requestPermission() async {
    await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
  }

  static Future<void> registrarTokenActual() async {
    final token = await FirebaseMessaging.instance.getToken();
    if (token != null) {
      await registrarToken(token);
    }
  }

  static Future<void> registrarToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    final authToken = prefs.getString('ev_token');
    if (authToken == null || authToken.isEmpty) return;

    final platform = Platform.isAndroid
        ? 'android'
        : Platform.isIOS
            ? 'ios'
            : 'other';

    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/notificaciones/fcm-token'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $authToken',
      },
      body: jsonEncode({
        'token': token,
        'platform': platform,
      }),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      print('No se pudo registrar FCM token: ${response.body}');
    }
  }

  static Future<void> _showForegroundNotification(RemoteMessage message) async {
    final notification = message.notification;
    final android = notification?.android;

    if (notification == null || android == null) return;

    await _localNotifications.show(
      id: notification.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: NotificationDetails(
        android: AndroidNotificationDetails(
          _channel.id,
          _channel.name,
          channelDescription: _channel.description,
          importance: Importance.max,
          priority: Priority.high,
          icon: android.smallIcon,
        ),
      ),
      payload: jsonEncode(message.data),
    );
  }
}
