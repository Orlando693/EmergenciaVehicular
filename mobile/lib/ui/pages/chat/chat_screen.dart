import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../core/api_config.dart';
import '../../../core/services/auth_service.dart';
import '../../../core/services/chat_service.dart';
import '../../shared/colors.dart';

class ChatScreen extends StatefulWidget {
  final int idIncidente;

  const ChatScreen({Key? key, required this.idIncidente}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<dynamic> _mensajes = [];
  final TextEditingController _mensajeController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isLoading = true;
  String _miNombre = '';
  int? _miIdUsuario;

  @override
  void initState() {
    super.initState();
    _cargarSesion();
    _cargarHistorial();
  }

  Future<void> _cargarSesion() async {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString('ev_user');

    if (userData != null) {
      final jsonUser = jsonDecode(userData);
      if (!mounted) return;
      setState(() {
        _miNombre = jsonUser['nombre']?.toString() ?? '';
        _miIdUsuario = jsonUser['id_usuario'];
      });
      return;
    }

    _miNombre = AuthService.currentUser?.nombre ?? '';
    _miIdUsuario = AuthService.currentUser?.idUsuario;
  }

  Future<void> _cargarHistorial() async {
    try {
      final historial = await ChatHttpService.obtenerHistorial(
        widget.idIncidente,
      );
      if (!mounted) return;
      setState(() {
        _mensajes.addAll(historial.reversed.toList());
        _isLoading = false;
      });
      _conectarWebSocket();
    } catch (e) {
      print('Error cargando historial: $e');
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _conectarWebSocket() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('ev_token');
    if (token == null) return;

    final wsBase = ApiConfig.baseUrl.replaceFirst('http', 'ws');
    final wsUrl = '$wsBase/chat/${widget.idIncidente}/ws?token=$token';

    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _subscription = _channel!.stream.listen(
        (data) {
          final msj = jsonDecode(data);
          if (!mounted) return;
          setState(() {
            _mensajes.insert(0, msj);
          });
        },
        onError: (error) {
          print('WebSocket Error: $error');
        },
        onDone: () {
          print('WebSocket desconectado');
        },
      );
    } catch (e) {
      print('Error estableciendo websocket: $e');
    }
  }

  void _enviarMensaje() {
    final texto = _mensajeController.text.trim();
    if (texto.isEmpty || _channel == null) return;

    _channel!.sink.add(jsonEncode({'contenido': texto}));
    _mensajeController.clear();
    FocusScope.of(context).unfocus();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _channel?.sink.close();
    _mensajeController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: AppBar(
        title: Text('Chat - Incidente #${widget.idIncidente}'),
        backgroundColor: AppColors.slate800,
        elevation: 0,
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      color: AppColors.orange500,
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    reverse: true,
                    padding: const EdgeInsets.only(top: 8, bottom: 8),
                    itemCount: _mensajes.length,
                    itemBuilder: (context, index) {
                      final msj = _mensajes[index];
                      final esSistema = msj['tipo'] == 'sistema';
                      final esMio = msj['nombre_emisor'] == _miNombre ||
                          msj['id_usuario'] == _miIdUsuario;

                      if (esSistema) {
                        return _mensajeSistema(msj['contenido'] ?? '');
                      }

                      return _burbujaMensaje(msj, esMio);
                    },
                  ),
          ),
          _inputCaja(),
        ],
      ),
    );
  }

  Widget _mensajeSistema(String contenido) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.slate800,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            contenido,
            style: const TextStyle(color: Colors.white54, fontSize: 12),
          ),
        ),
      ),
    );
  }

  Widget _burbujaMensaje(dynamic msj, bool esMio) {
    final nombreRemitente = msj['nombre_emisor'] ?? 'Usuario';
    final alinear = esMio ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final colorFondo = esMio ? AppColors.orange600 : AppColors.slate800;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: alinear,
        children: [
          Text(
            nombreRemitente,
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.75,
            ),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: colorFondo,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              msj['contenido'] ?? '',
              style: const TextStyle(color: Colors.white, fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _inputCaja() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
      color: AppColors.slate800,
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _mensajeController,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: 'Escribe un mensaje...',
                  hintStyle: const TextStyle(color: Colors.white54),
                  fillColor: AppColors.slate900,
                  filled: true,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                ),
                onSubmitted: (_) => _enviarMensaje(),
              ),
            ),
            const SizedBox(width: 8),
            CircleAvatar(
              backgroundColor: AppColors.orange500,
              radius: 24,
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white),
                onPressed: _enviarMensaje,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
