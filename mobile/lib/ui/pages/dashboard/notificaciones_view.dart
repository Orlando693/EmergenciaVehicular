import 'package:flutter/material.dart';
import '../../../core/services/notificacion_service.dart';
import '../../shared/colors.dart';
import '../chat/chat_screen.dart';

class NotificacionesView extends StatefulWidget {
  const NotificacionesView({Key? key}) : super(key: key);

  @override
  State<NotificacionesView> createState() => _NotificacionesViewState();
}

class _NotificacionesViewState extends State<NotificacionesView> {
  List<dynamic> _notificaciones = [];
  int _noLeidas = 0;
  bool _isLoading = true;
  bool _marcando = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    try {
      final data = await NotificacionService.listar();
      if (!mounted) return;
      setState(() {
        _notificaciones = data['items'] ?? [];
        _noLeidas = data['no_leidas'] ?? 0;
        _isLoading = false;
      });
    } catch (e) {
      print('Error cargando notificaciones: $e');
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _marcarTodas() async {
    setState(() => _marcando = true);
    try {
      await NotificacionService.marcarTodasLeidas();
      await _cargar();
    } catch (e) {
      print('Error marcando notificaciones: $e');
    } finally {
      if (mounted) setState(() => _marcando = false);
    }
  }

  Future<void> _abrir(dynamic item) async {
    final idNotif = item['id_notificacion'];
    if (idNotif is int && item['leida'] != true) {
      try {
        await NotificacionService.marcarLeida(idNotif);
      } catch (e) {
        print('Error marcando notificacion: $e');
      }
    }

    final idIncidente = item['id_incidente'];
    if (!mounted) return;
    if (idIncidente is int) {
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ChatScreen(idIncidente: idIncidente),
        ),
      );
    }
    _cargar();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.orange500),
      );
    }

    return RefreshIndicator(
      color: AppColors.orange500,
      backgroundColor: AppColors.slate800,
      onRefresh: _cargar,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
        children: [
          _SummaryCard(
            total: _notificaciones.length,
            unread: _noLeidas,
            marking: _marcando,
            onMarkAll: _noLeidas == 0 ? null : _marcarTodas,
          ),
          const SizedBox(height: 16),
          if (_notificaciones.isEmpty)
            const _EmptyNotifications()
          else
            ..._notificaciones.map(
              (item) => _NotificationTile(
                item: item,
                onTap: () => _abrir(item),
              ),
            ),
        ],
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.total,
    required this.unread,
    required this.marking,
    required this.onMarkAll,
  });

  final int total;
  final int unread;
  final bool marking;
  final VoidCallback? onMarkAll;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const CircleAvatar(
                backgroundColor: AppColors.orange500,
                child: Icon(Icons.notifications_active, color: Colors.white),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Centro de notificaciones',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$unread sin leer de $total notificaciones',
                      style: const TextStyle(
                        color: AppColors.slate400,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (unread > 0) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: marking ? null : onMarkAll,
              icon: marking
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.orange500,
                      ),
                    )
                  : const Icon(Icons.done_all, color: AppColors.orange500),
              label: const Text(
                'Marcar todas como leidas',
                style: TextStyle(color: AppColors.orange500),
              ),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppColors.orange500),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item, required this.onTap});

  final dynamic item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final leida = item['leida'] == true;

    return Card(
      color: leida ? AppColors.slate800 : AppColors.blue950,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        leading: Icon(
          leida ? Icons.notifications_none : Icons.notifications_active,
          color: leida ? AppColors.slate400 : AppColors.orange500,
        ),
        title: Text(
          item['titulo']?.toString() ?? 'Notificacion',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Text(
          item['mensaje']?.toString() ?? '',
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: AppColors.slate400),
        ),
        trailing: item['id_incidente'] is int
            ? const Icon(Icons.chevron_right, color: AppColors.slate400)
            : null,
        onTap: onTap,
      ),
    );
  }
}

class _EmptyNotifications extends StatelessWidget {
  const _EmptyNotifications();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(top: 90),
      child: Column(
        children: [
          Icon(Icons.notifications_off, size: 72, color: AppColors.slate500),
          SizedBox(height: 14),
          Text(
            'Sin notificaciones por ahora.',
            style: TextStyle(color: Colors.white, fontSize: 17),
          ),
          SizedBox(height: 6),
          Text(
            'Los cambios de estado y avisos apareceran aqui.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.slate400),
          ),
        ],
      ),
    );
  }
}
