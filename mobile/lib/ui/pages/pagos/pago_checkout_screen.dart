import 'package:flutter/material.dart';

import '../../../core/services/pago_service.dart';
import '../../shared/colors.dart';

class PagoCheckoutScreen extends StatefulWidget {
  final int idIncidente;

  const PagoCheckoutScreen({Key? key, required this.idIncidente})
      : super(key: key);

  @override
  State<PagoCheckoutScreen> createState() => _PagoCheckoutScreenState();
}

class _PagoCheckoutScreenState extends State<PagoCheckoutScreen> {
  final _formKey = GlobalKey<FormState>();
  final _numeroController = TextEditingController();
  final _titularController = TextEditingController();
  final _vencimientoController = TextEditingController();
  final _cvvController = TextEditingController();

  Map<String, dynamic>? _info;
  bool _loading = true;
  bool _paying = false;
  String _metodo = 'TARJETA';
  String? _error;

  @override
  void initState() {
    super.initState();
    _numeroController.text = '4111111111111111';
    _titularController.text = 'Cliente Emergencia';
    _vencimientoController.text = '12/30';
    _cvvController.text = '123';
    _cargarInfo();
  }

  @override
  void dispose() {
    _numeroController.dispose();
    _titularController.dispose();
    _vencimientoController.dispose();
    _cvvController.dispose();
    super.dispose();
  }

  Future<void> _cargarInfo() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await PagoService.infoIncidente(widget.idIncidente);
      if (!mounted) return;
      setState(() {
        _info = data;
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

  Future<void> _pagar() async {
    if (_metodo == 'TARJETA' && !(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() => _paying = true);
    try {
      final pago = await PagoService.pagarIncidente(
        idIncidente: widget.idIncidente,
        metodoPago: _metodo,
        numeroTarjeta: _metodo == 'TARJETA' ? _numeroController.text : null,
        nombreTitular: _metodo == 'TARJETA' ? _titularController.text : null,
        vencimiento: _metodo == 'TARJETA' ? _vencimientoController.text : null,
        cvv: _metodo == 'TARJETA' ? _cvvController.text : null,
      );

      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: AppColors.slate800,
          title: const Text('Pago registrado', style: TextStyle(color: Colors.white)),
          content: Text(
            'Estado: ${pago['estado'] ?? 'COMPLETADO'}\nReferencia: ${pago['referencia'] ?? '-'}',
            style: const TextStyle(color: Colors.white70),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Aceptar'),
            ),
          ],
        ),
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: AppBar(
        backgroundColor: AppColors.slate800,
        elevation: 0,
        title: Text('Pago incidente #${widget.idIncidente}'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.orange500))
          : _error != null
              ? _errorView()
              : _content(),
    );
  }

  Widget _errorView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppColors.red500, size: 52),
            const SizedBox(height: 12),
            Text(
              _error ?? 'No se pudo cargar el pago.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _cargarInfo,
              child: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _content() {
    final pagoExistente = _info?['pago_existente'];
    final yaPagado = pagoExistente != null &&
        pagoExistente['estado']?.toString().toUpperCase() == 'COMPLETADO';

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _resumenCard(yaPagado: yaPagado),
        const SizedBox(height: 16),
        if (yaPagado)
          _pagoExistenteCard(pagoExistente)
        else ...[
          _metodosCard(),
          const SizedBox(height: 16),
          if (_metodo == 'TARJETA') _tarjetaForm(),
          const SizedBox(height: 20),
          SizedBox(
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _paying ? null : _pagar,
              icon: _paying
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.lock_outline),
              label: Text(_paying ? 'Procesando...' : 'Confirmar pago'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.orange500,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Pago simulado. Para probar fallo usa una tarjeta terminada en 0000.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.slate400, fontSize: 12),
          ),
        ],
      ],
    );
  }

  Widget _resumenCard({required bool yaPagado}) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.receipt_long, color: AppColors.orange500),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  yaPagado ? 'Servicio pagado' : 'Resumen de pago',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          _moneyRow('Total', _info?['monto_total'], strong: true),
          _moneyRow('Taller', _info?['monto_taller']),
          _moneyRow('Comision plataforma', _info?['comision_plataforma']),
          const SizedBox(height: 10),
          Text(
            'Clasificacion IA: ${_info?['clasificacion_ia'] ?? 'Sin clasificacion'}',
            style: const TextStyle(color: AppColors.slate400, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _moneyRow(String label, dynamic value, {bool strong = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.slate400)),
          Text(
            'Bs ${_money(value)}',
            style: TextStyle(
              color: strong ? AppColors.orange400 : Colors.white,
              fontSize: strong ? 20 : 15,
              fontWeight: strong ? FontWeight.bold : FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _pagoExistenteCard(dynamic pago) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.green.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.green.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.check_circle, color: Colors.green),
              SizedBox(width: 10),
              Text(
                'Pago aprobado',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'Metodo: ${pago['metodo_pago'] ?? '-'}\nReferencia: ${pago['referencia'] ?? '-'}',
            style: const TextStyle(color: Colors.white70, height: 1.35),
          ),
        ],
      ),
    );
  }

  Widget _metodosCard() {
    final methods = [
      ('TARJETA', Icons.credit_card, 'Tarjeta'),
      ('TRANSFERENCIA', Icons.account_balance, 'Transferencia'),
      ('EFECTIVO', Icons.payments_outlined, 'Efectivo'),
    ];

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Metodo de pago',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ...methods.map((m) {
            final selected = _metodo == m.$1;
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () => setState(() => _metodo = m.$1),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: selected
                        ? AppColors.orange500.withValues(alpha: 0.16)
                        : AppColors.slate900.withValues(alpha: 0.35),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: selected ? AppColors.orange500 : AppColors.slate700,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(m.$2, color: selected ? AppColors.orange500 : AppColors.slate400),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          m.$3,
                          style: TextStyle(
                            color: selected ? Colors.white : AppColors.slate400,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      if (selected)
                        const Icon(Icons.check_circle, color: AppColors.orange500),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _tarjetaForm() {
    return Form(
      key: _formKey,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.slate800,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.slate700),
        ),
        child: Column(
          children: [
            _input(
              controller: _numeroController,
              label: 'Numero de tarjeta',
              keyboardType: TextInputType.number,
              validator: (v) {
                final raw = (v ?? '').replaceAll(' ', '');
                if (raw.length < 12) return 'Numero incompleto';
                return null;
              },
            ),
            _input(
              controller: _titularController,
              label: 'Titular',
              validator: (v) => (v ?? '').trim().isEmpty ? 'Campo requerido' : null,
            ),
            Row(
              children: [
                Expanded(
                  child: _input(
                    controller: _vencimientoController,
                    label: 'MM/AA',
                    validator: (v) => (v ?? '').trim().isEmpty ? 'Requerido' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _input(
                    controller: _cvvController,
                    label: 'CVV',
                    keyboardType: TextInputType.number,
                    validator: (v) => (v ?? '').length < 3 ? 'CVV' : null,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _input({
    required TextEditingController controller,
    required String label,
    String? Function(String?)? validator,
    TextInputType? keyboardType,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        validator: validator,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: AppColors.slate400),
          filled: true,
          fillColor: AppColors.slate900.withValues(alpha: 0.45),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          errorStyle: const TextStyle(color: AppColors.red400),
        ),
      ),
    );
  }

  String _money(dynamic value) {
    final n = num.tryParse(value?.toString() ?? '0') ?? 0;
    return n.toStringAsFixed(2);
  }
}
