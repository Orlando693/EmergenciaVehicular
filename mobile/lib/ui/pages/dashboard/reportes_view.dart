import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../../../core/services/reportes_service.dart';
import '../../shared/colors.dart';

class ReportesView extends StatefulWidget {
  const ReportesView({Key? key}) : super(key: key);

  @override
  State<ReportesView> createState() => _ReportesViewState();
}

class _ReportesViewState extends State<ReportesView> {
  final AudioRecorder _recorder = AudioRecorder();

  Map<String, dynamic>? _resumen;
  Map<String, dynamic>? _pagos;
  Map<String, dynamic>? _incidentes;
  Map<String, dynamic>? _usuarios;
  Map<String, dynamic>? _talleres;
  bool _loading = true;
  bool _recording = false;
  bool _sendingAudio = false;
  String? _error;
  String? _lastAudioUrl;
  String? _lastTranscript;
  String? _lastIaResponse;
  String _activeReport = 'resumen';

  @override
  void initState() {
    super.initState();
    _cargarReportes();
  }

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _cargarReportes() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await Future.wait([
        ReportesService.resumen(),
        ReportesService.pagos(),
        ReportesService.incidentes(),
        ReportesService.usuarios(),
        ReportesService.talleres(),
      ]);
      if (!mounted) return;
      setState(() {
        _resumen = data[0];
        _pagos = data[1];
        _incidentes = data[2];
        _usuarios = data[3];
        _talleres = data[4];
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

  Future<void> _toggleAudio() async {
    if (_recording) {
      try {
        final path = await _recorder.stop();
        if (!mounted) return;
        setState(() => _recording = false);
        if (path != null) {
          await _enviarAudio(File(path));
        }
      } catch (e) {
        if (!mounted) return;
        setState(() => _recording = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('No se pudo detener la grabacion: $e')),
        );
      }
      return;
    }

    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Permite acceso al microfono para grabar.')),
      );
      return;
    }

    final dir = await getTemporaryDirectory();
    final path =
        '${dir.path}/reporte_admin_${DateTime.now().millisecondsSinceEpoch}.m4a';
    try {
      await _recorder.start(
        const RecordConfig(encoder: AudioEncoder.aacLc),
        path: path,
      );
      if (mounted) setState(() => _recording = true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudo iniciar el microfono: $e')),
      );
    }
  }

  Future<void> _enviarAudio(File file) async {
    setState(() => _sendingAudio = true);
    try {
      final result = await ReportesService.subirAudio(file);
      if (!mounted) return;
      final intencion = _normalizeReport(result['intencion']?.toString());
      setState(() {
        _lastAudioUrl = result['url']?.toString();
        _lastTranscript = result['transcripcion']?.toString();
        _lastIaResponse = result['respuesta_ia']?.toString();
        if (intencion != 'desconocido') {
          _activeReport = intencion;
        }
        _sendingAudio = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            intencion == 'desconocido'
                ? 'Audio enviado, pero no se detecto el reporte solicitado.'
                : 'IA detecto reporte de $intencion.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _sendingAudio = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error enviando audio: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.orange500),
      );
    }

    if (_error != null) {
      return _errorView();
    }

    return RefreshIndicator(
      color: AppColors.orange500,
      backgroundColor: AppColors.slate800,
      onRefresh: _cargarReportes,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
        children: [
          _header(),
          const SizedBox(height: 16),
          _audioCard(),
          const SizedBox(height: 16),
          _reportSelector(),
          const SizedBox(height: 16),
          _activeReportBody(),
        ],
      ),
    );
  }

  Widget _header() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.blue950, AppColors.slate800],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.slate700),
      ),
      child: const Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.orange500,
            child: Icon(Icons.analytics_outlined, color: Colors.white),
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Reportes administrativos',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Resumen operativo, pagos y reporte rapido por audio.',
                  style: TextStyle(color: AppColors.slate400, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _audioCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: _recording
            ? AppColors.red500.withValues(alpha: 0.12)
            : AppColors.slate800,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: _recording ? AppColors.red400 : AppColors.slate700,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _recording ? Icons.mic : Icons.mic_none,
                color: _recording ? AppColors.red400 : AppColors.orange500,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _recording ? 'Grabando reporte...' : 'Reporte por audio',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Graba una observacion administrativa y enviala al backend. El audio queda guardado en uploads y registrado en bitacora.',
            style: TextStyle(color: AppColors.slate400, height: 1.35),
          ),
          if (_lastAudioUrl != null) ...[
            const SizedBox(height: 10),
            Text(
              'Ultimo audio: $_lastAudioUrl',
              style: const TextStyle(color: AppColors.orange400, fontSize: 12),
            ),
          ],
          if (_lastTranscript != null && _lastTranscript!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Escuchado: "$_lastTranscript"',
              style: const TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ],
          if (_lastIaResponse != null && _lastIaResponse!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              _lastIaResponse!,
              style: const TextStyle(color: AppColors.slate400, fontSize: 12),
            ),
          ],
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _sendingAudio ? null : _toggleAudio,
              icon: _sendingAudio
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : Icon(_recording ? Icons.stop : Icons.mic),
              label: Text(
                _sendingAudio
                    ? 'Enviando audio...'
                    : _recording
                        ? 'Detener y enviar'
                        : 'Grabar reporte',
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    _recording ? AppColors.red500 : AppColors.orange500,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _reportSelector() {
    final options = [
      ('resumen', 'Resumen', Icons.dashboard_outlined),
      ('usuarios', 'Usuarios', Icons.group),
      ('pagos', 'Pagos', Icons.payments_outlined),
      ('incidentes', 'Incidentes', Icons.warning_amber_rounded),
      ('talleres', 'Talleres', Icons.build),
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: options.map((item) {
          final selected = _activeReport == item.$1;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              selected: selected,
              label: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    item.$3,
                    size: 16,
                    color: selected ? Colors.white : AppColors.slate400,
                  ),
                  const SizedBox(width: 6),
                  Text(item.$2),
                ],
              ),
              labelStyle: TextStyle(
                color: selected ? Colors.white : AppColors.slate400,
                fontWeight: FontWeight.w700,
              ),
              selectedColor: AppColors.orange500,
              backgroundColor: AppColors.slate800,
              side: BorderSide(
                color: selected ? AppColors.orange500 : AppColors.slate700,
              ),
              onSelected: (_) => setState(() => _activeReport = item.$1),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _activeReportBody() {
    switch (_activeReport) {
      case 'usuarios':
        return _usuariosReport();
      case 'pagos':
        return _pagosReport();
      case 'incidentes':
        return _incidentesReport();
      case 'talleres':
        return _talleresReport();
      case 'resumen':
      default:
        return Column(
          children: [
            _statsGrid(),
            const SizedBox(height: 16),
            _sectionCard(
              title: 'Resumen general',
              icon: Icons.dashboard_outlined,
              children: [
                _metricRow('Incidentes reportados', _number(_resumen?['incidentes_reportados'])),
                _metricRow('Incidentes en proceso', _number(_resumen?['incidentes_en_proceso'])),
                _metricRow('Incidentes resueltos', _number(_resumen?['incidentes_resueltos'])),
                _metricRow('Pagos completados', _number(_resumen?['total_pagos_completados'])),
              ],
            ),
          ],
        );
    }
  }

  Widget _usuariosReport() {
    final porRol = (_usuarios?['por_rol'] ?? {}) as Map<String, dynamic>;
    final items = (_usuarios?['items'] ?? []) as List<dynamic>;
    return _sectionCard(
      title: 'Reporte de usuarios',
      icon: Icons.group,
      children: [
        _metricRow('Total usuarios', _number(_usuarios?['total'])),
        _metricRow('Clientes', _number(porRol['CLIENTE'])),
        _metricRow('Talleres', _number(porRol['TALLER'])),
        _metricRow('Administradores', _number(porRol['ADMINISTRADOR'])),
        const SizedBox(height: 8),
        ...items.take(6).map((u) => _miniItem(
              '${u['nombres'] ?? ''} ${u['apellidos'] ?? ''}'.trim(),
              '${u['email'] ?? '-'} · ${u['rol'] ?? '-'} · ${u['estado'] ?? '-'}',
            )),
      ],
    );
  }

  Widget _pagosReport() {
    return _sectionCard(
      title: 'Reporte de pagos',
      icon: Icons.payments_outlined,
      children: [
        _metricRow('Total pagos', _number(_pagos?['total'])),
        _metricRow('Monto total', 'Bs ${_money(_pagos?['monto_total'])}'),
        _metricRow('Comision plataforma', 'Bs ${_money(_pagos?['comision_total'])}'),
      ],
    );
  }

  Widget _incidentesReport() {
    final porEstado = (_incidentes?['por_estado'] ?? {}) as Map<String, dynamic>;
    return _sectionCard(
      title: 'Reporte de incidentes',
      icon: Icons.warning_amber_rounded,
      children: [
        _metricRow('Total filtrado', _number(_incidentes?['total'])),
        _metricRow('Reportados', _number(porEstado['REPORTADO'])),
        _metricRow('En proceso', _number(porEstado['EN_PROCESO'])),
        _metricRow('Resueltos', _number(porEstado['RESUELTO'])),
        _metricRow('Pagados', _number(porEstado['PAGADO'])),
      ],
    );
  }

  Widget _talleresReport() {
    final items = (_talleres?['items'] ?? []) as List<dynamic>;
    return _sectionCard(
      title: 'Reporte de talleres',
      icon: Icons.build,
      children: [
        _metricRow('Total talleres', _number(_talleres?['total'])),
        _metricRow('Ingresos talleres', 'Bs ${_money(_talleres?['total_ingresos'])}'),
        const SizedBox(height: 8),
        ...items.take(6).map((t) => _miniItem(
              t['razon_social']?.toString() ?? 'Taller',
              '${t['estado_registro'] ?? '-'} · servicios: ${t['total_servicios'] ?? 0} · Bs ${_money(t['ingresos_taller'])}',
            )),
      ],
    );
  }

  Widget _statsGrid() {
    return GridView.count(
      crossAxisCount: 2,
      childAspectRatio: 1.45,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      children: [
        _statCard('Incidentes', _number(_resumen?['total_incidentes']), Icons.report),
        _statCard('Usuarios', _number(_resumen?['total_usuarios']), Icons.group),
        _statCard('Talleres', _number(_resumen?['total_talleres']), Icons.build),
        _statCard(
          'Ingresos',
          'Bs ${_money(_resumen?['ingresos_totales'])}',
          Icons.trending_up,
        ),
      ],
    );
  }

  Widget _statCard(String label, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Icon(icon, color: AppColors.orange500),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(label, style: const TextStyle(color: AppColors.slate400)),
        ],
      ),
    );
  }

  Widget _sectionCard({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(icon, color: AppColors.orange500),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }

  Widget _metricRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(label, style: const TextStyle(color: AppColors.slate400)),
          ),
          Text(
            value,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  Widget _miniItem(String title, String subtitle) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.slate900.withValues(alpha: 0.45),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title.isEmpty ? 'Sin nombre' : title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            subtitle,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.slate400, fontSize: 12),
          ),
        ],
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
          _error ?? 'Error cargando reportes.',
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.white70),
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: _cargarReportes,
          icon: const Icon(Icons.refresh),
          label: const Text('Reintentar'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.orange500,
            foregroundColor: Colors.white,
          ),
        ),
      ],
    );
  }

  String _money(dynamic value) {
    final n = num.tryParse(value?.toString() ?? '0') ?? 0;
    return n.toStringAsFixed(2);
  }

  String _number(dynamic value) {
    final n = num.tryParse(value?.toString() ?? '0') ?? 0;
    return n.toInt().toString();
  }

  String _normalizeReport(String? value) {
    final text = (value ?? '').toLowerCase().trim();
    if (text.contains('usuario') || text.contains('cliente') || text.contains('admin')) {
      return 'usuarios';
    }
    if (text.contains('pago') || text.contains('cobro') || text.contains('ingreso') || text.contains('qr')) {
      return 'pagos';
    }
    if (text.contains('incidente') || text.contains('caso') || text.contains('alerta')) {
      return 'incidentes';
    }
    if (text.contains('taller') || text.contains('mecanico')) {
      return 'talleres';
    }
    if (text.contains('resumen') || text.contains('general')) {
      return 'resumen';
    }
    return 'desconocido';
  }
}
