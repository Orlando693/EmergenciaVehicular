import 'package:flutter/material.dart';
import '../../../core/services/incidente_service.dart';
import '../../../core/services/vehiculo_service.dart';
import '../../shared/colors.dart';
import '../vehiculos/mis_vehiculos_screen.dart';

class CrearIncidenteScreen extends StatefulWidget {
  const CrearIncidenteScreen({Key? key}) : super(key: key);

  @override
  State<CrearIncidenteScreen> createState() => _CrearIncidenteScreenState();
}

class _CrearIncidenteScreenState extends State<CrearIncidenteScreen> {
  final _descripcionController = TextEditingController();
  List<dynamic> _vehiculos = [];
  int? _vehiculoSeleccionado;
  bool _isLoading = true;
  bool _isEnviando = false;

  @override
  void initState() {
    super.initState();
    _cargarVehiculos();
  }

  Future<void> _cargarVehiculos() async {
    try {
      final data = await VehiculoService.misVehiculos();
      if (!mounted) return;
      setState(() {
        _vehiculos = data.where((v) => v['activo'] != false).toList();
        _vehiculoSeleccionado = _vehiculos.isNotEmpty
            ? _vehiculos.first['id_vehiculo']
            : null;
        _isLoading = false;
      });
    } catch (e) {
      print('Error cargando vehiculos: $e');
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _abrirVehiculos() async {
    final creado = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const MisVehiculosScreen()),
    );

    if (creado == true) {
      setState(() => _isLoading = true);
      await _cargarVehiculos();
    }
  }

  Future<void> _generarDiagnostico() async {
    if (_vehiculoSeleccionado == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Primero registra un vehiculo.')),
      );
      return;
    }

    if (_descripcionController.text.trim().length <= 10) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Describe el problema con mas detalle (minimo 10 caracteres).',
          ),
        ),
      );
      return;
    }

    setState(() => _isEnviando = true);

    try {
      final response = await IncidenteService.registrarIncidente(
        idVehiculo: _vehiculoSeleccionado!,
        descripcion: _descripcionController.text.trim(),
        ubicacionLat: 0.0,
        ubicacionLng: 0.0,
      );

      if (!mounted) return;
      await _mostrarResultadoIa(response);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) {
        setState(() => _isEnviando = false);
      }
    }
  }

  Future<void> _mostrarResultadoIa(Map<String, dynamic> incidente) async {
    final clasificacion =
        incidente['clasificacion_ia']?.toString() ?? 'Sin clasificacion';
    final resumen = incidente['resumen_ia']?.toString() ??
        'La IA no devolvio un resumen para este incidente.';
    final idIncidente = incidente['id_incidente'];

    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          backgroundColor: AppColors.slate800,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          title: Row(
            children: [
              const Icon(Icons.psychology_alt, color: AppColors.orange500),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Diagnostico IA #$idIncidente',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Clasificacion',
                  style: TextStyle(color: AppColors.slate400, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Text(
                  clasificacion,
                  style: const TextStyle(
                    color: AppColors.orange500,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Resumen y recomendacion',
                  style: TextStyle(color: AppColors.slate400, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Text(
                  resumen,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                Navigator.of(this.context).pop(incidente);
              },
              child: const Text(
                'Ver mis alertas',
                style: TextStyle(color: AppColors.orange500),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _descripcionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppColors.slate900,
        body: Center(
          child: CircularProgressIndicator(color: AppColors.orange500),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: AppBar(
        title: const Text('Generar alerta IA'),
        backgroundColor: AppColors.slate800,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '1. Selecciona el vehiculo',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            if (_vehiculos.isEmpty)
              _SinVehiculosCard(onTap: _abrirVehiculos)
            else
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: AppColors.slate800,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<int>(
                    isExpanded: true,
                    dropdownColor: AppColors.slate800,
                    value: _vehiculoSeleccionado,
                    hint: const Text(
                      'Mis vehiculos',
                      style: TextStyle(color: Colors.white54),
                    ),
                    items: _vehiculos.map<DropdownMenuItem<int>>((v) {
                      return DropdownMenuItem<int>(
                        value: v['id_vehiculo'],
                        child: Text(
                          '${v['marca']} ${v['modelo']} (${v['placa']})',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: Colors.white),
                        ),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() => _vehiculoSeleccionado = value);
                    },
                  ),
                ),
              ),
            if (_vehiculos.isNotEmpty) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: _abrirVehiculos,
                  icon: const Icon(Icons.add, color: AppColors.orange500),
                  label: const Text(
                    'Agregar otro vehiculo',
                    style: TextStyle(color: AppColors.orange500),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 24),
            const Text(
              '2. Describe la emergencia para la IA',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _descripcionController,
              maxLines: 5,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText:
                    'Ej. Mi auto saco humo blanco del capo y huele a plastico quemado...',
                hintStyle: const TextStyle(color: Colors.white54),
                filled: true,
                fillColor: AppColors.slate800,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.orange500.withValues(alpha: 0.1),
                border: Border.all(
                  color: AppColors.orange500.withValues(alpha: 0.3),
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.location_off,
                    color: AppColors.orange500,
                    size: 24,
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Ubicacion GPS opcional: por ahora se enviara en cero para acelerar la solicitud.',
                      style: TextStyle(
                        color: AppColors.orange500,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.orange500,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: _isEnviando || _vehiculos.isEmpty
                    ? null
                    : _generarDiagnostico,
                icon: _isEnviando
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Icon(Icons.psychology_alt, color: Colors.white),
                label: Text(
                  _isEnviando ? 'Analizando con IA...' : 'Generar diagnostico IA',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
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

class _SinVehiculosCard extends StatelessWidget {
  const _SinVehiculosCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Column(
        children: [
          const Icon(Icons.directions_car, color: AppColors.orange500, size: 42),
          const SizedBox(height: 12),
          const Text(
            'Necesitas registrar un vehiculo',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'La IA usa la marca, modelo y placa para crear una alerta coherente.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.slate400, fontSize: 12),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: onTap,
              icon: const Icon(Icons.add, color: Colors.white),
              label: const Text(
                'Registrar vehiculo',
                style: TextStyle(color: Colors.white),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.orange500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
