import 'package:flutter/material.dart';

import '../../../core/services/pago_service.dart';
import '../../shared/colors.dart';

class MisPagosScreen extends StatefulWidget {
  final bool showAppBar;

  const MisPagosScreen({Key? key, this.showAppBar = true}) : super(key: key);

  @override
  State<MisPagosScreen> createState() => _MisPagosScreenState();
}

class _MisPagosScreenState extends State<MisPagosScreen> {
  List<dynamic> _pagos = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await PagoService.misPagos();
      if (!mounted) return;
      setState(() {
        _pagos = data['items'] ?? [];
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: widget.showAppBar
          ? AppBar(
              title: const Text('Mis pagos'),
              backgroundColor: AppColors.slate800,
              elevation: 0,
            )
          : null,
      body: RefreshIndicator(
        color: AppColors.orange500,
        backgroundColor: AppColors.slate800,
        onRefresh: _cargar,
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: AppColors.orange500))
            : _error != null
                ? _errorView()
                : _pagos.isEmpty
                    ? _emptyView()
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                        itemCount: _pagos.length,
                        itemBuilder: (_, index) => _pagoCard(_pagos[index]),
                      ),
      ),
    );
  }

  Widget _errorView() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 100),
        const Icon(Icons.error_outline, size: 64, color: AppColors.red500),
        const SizedBox(height: 12),
        Text(
          _error ?? 'Error al cargar pagos.',
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.white70),
        ),
      ],
    );
  }

  Widget _emptyView() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: const [
        SizedBox(height: 110),
        Icon(Icons.receipt_long, size: 72, color: AppColors.slate500),
        SizedBox(height: 14),
        Text(
          'Todavia no tienes pagos registrados.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white, fontSize: 17),
        ),
      ],
    );
  }

  Widget _pagoCard(dynamic pago) {
    final estado = pago['estado']?.toString() ?? 'DESCONOCIDO';
    final aprobado = estado.toUpperCase() == 'COMPLETADO';

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                aprobado ? Icons.check_circle : Icons.schedule,
                color: aprobado ? Colors.green : AppColors.orange500,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Incidente #${pago['id_incidente']}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Text(
                estado,
                style: TextStyle(
                  color: aprobado ? Colors.green : AppColors.orange400,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Bs ${_money(pago['monto_total'])}',
            style: const TextStyle(
              color: AppColors.orange400,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Metodo: ${pago['metodo_pago'] ?? '-'}\nReferencia: ${pago['referencia'] ?? '-'}',
            style: const TextStyle(color: AppColors.slate400, height: 1.35),
          ),
        ],
      ),
    );
  }

  String _money(dynamic value) {
    final n = num.tryParse(value?.toString() ?? '0') ?? 0;
    return n.toStringAsFixed(2);
  }
}
