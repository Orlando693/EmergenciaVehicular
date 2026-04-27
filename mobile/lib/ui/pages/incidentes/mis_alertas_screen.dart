import 'package:flutter/material.dart';
import '../../../core/services/incidente_service.dart';
import '../../shared/colors.dart';
import '../chat/chat_screen.dart';

class MisAlertasScreen extends StatefulWidget {
  final bool showAppBar;

  const MisAlertasScreen({Key? key, this.showAppBar = true}) : super(key: key);

  @override
  State<MisAlertasScreen> createState() => _MisAlertasScreenState();
}

class _MisAlertasScreenState extends State<MisAlertasScreen> {
  List<dynamic> _historial = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _cargarAlertas();
  }

  Future<void> _cargarAlertas() async {
    try {
      final result = await IncidenteService.consultarHistorial();
      if (!mounted) return;
      setState(() {
        _historial = result;
        _isLoading = false;
      });
    } catch (e) {
      print('Error: $e');
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: widget.showAppBar
          ? AppBar(
              title: const Text('Mis Alertas y Chat'),
              backgroundColor: AppColors.slate800,
              elevation: 0,
            )
          : null,
      body: RefreshIndicator(
        color: AppColors.orange500,
        backgroundColor: AppColors.slate800,
        onRefresh: _cargarAlertas,
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.orange500),
              )
            : _historial.isEmpty
                ? _vacio()
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                    itemCount: _historial.length,
                    itemBuilder: (context, index) {
                      final item = _historial[index];
                      return _tarjetaIncidente(item);
                    },
                  ),
      ),
    );
  }

  Widget _vacio() {
    return ListView(
      children: const [
        SizedBox(height: 120),
        Icon(Icons.check_circle_outline, size: 80, color: AppColors.slate500),
        SizedBox(height: 16),
        Text(
          'No tienes alertas activas.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white, fontSize: 18),
        ),
        SizedBox(height: 8),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 32),
          child: Text(
            'Si ocurre una emergencia, usa el botón "S.O.S IA" de la pantalla principal.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.slate400),
          ),
        ),
      ],
    );
  }

  Widget _tarjetaIncidente(dynamic item) {
    var estadoColor = AppColors.blue500;
    final estado = item['estado']?.toString() ?? 'DESCONOCIDO';
    if (estado == 'ASIGNADO' || estado == 'EN_PROCESO') {
      estadoColor = AppColors.orange500;
    } else if (estado == 'RESUELTO') {
      estadoColor = Colors.green;
    } else if (estado == 'CANCELADO') {
      estadoColor = AppColors.red500;
    }

    return Card(
      color: AppColors.slate800,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    'Alerta #${item['id_incidente']}',
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: estadoColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: estadoColor.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    estado,
                    style: TextStyle(
                      color: estadoColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              item['descripcion'] ?? 'Sin descripción',
              style: const TextStyle(color: Colors.white54, fontSize: 14),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            if (item['clasificacion_ia'] != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(
                    Icons.psychology_alt,
                    color: AppColors.orange500,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'IA: ${item['clasificacion_ia']}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.orange500,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
            if (item['resumen_ia'] != null) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.blue950.withValues(alpha: 0.45),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.slate700),
                ),
                child: Text(
                  item['resumen_ia'],
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 13,
                    height: 1.3,
                  ),
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  final id = item['id_incidente'];
                  if (id is! int) return;

                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ChatScreen(idIncidente: id),
                    ),
                  );
                },
                icon: const Icon(Icons.chat_bubble_outline, color: Colors.white),
                label: const Text(
                  'Abrir chat en vivo',
                  style: TextStyle(color: Colors.white),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.slate400),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
