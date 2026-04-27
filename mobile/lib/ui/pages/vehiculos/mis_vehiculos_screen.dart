import 'package:flutter/material.dart';
import '../../../core/services/vehiculo_service.dart';
import '../../shared/colors.dart';

class MisVehiculosScreen extends StatefulWidget {
  final bool showAppBar;

  const MisVehiculosScreen({Key? key, this.showAppBar = true})
    : super(key: key);

  @override
  State<MisVehiculosScreen> createState() => _MisVehiculosScreenState();
}

class _MisVehiculosScreenState extends State<MisVehiculosScreen> {
  List<dynamic> _vehiculos = [];
  bool _isLoading = true;

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
        _vehiculos = data;
        _isLoading = false;
      });
    } catch (e) {
      print('Error cargando vehiculos: $e');
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _abrirFormulario() async {
    final creado = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const VehiculoFormScreen()),
    );

    if (creado == true) {
      await _cargarVehiculos();
      if (mounted && widget.showAppBar) {
        Navigator.of(context).pop(true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: widget.showAppBar
          ? AppBar(
              title: const Text('Mis vehiculos'),
              backgroundColor: AppColors.slate800,
              elevation: 0,
            )
          : null,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _abrirFormulario,
        backgroundColor: AppColors.orange500,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text('Agregar'),
      ),
      body: RefreshIndicator(
        color: AppColors.orange500,
        backgroundColor: AppColors.slate800,
        onRefresh: _cargarVehiculos,
        child: _isLoading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.orange500),
              )
            : _vehiculos.isEmpty
                ? _vacio()
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                    itemCount: _vehiculos.length,
                    itemBuilder: (context, index) {
                      return _VehiculoCard(vehiculo: _vehiculos[index]);
                    },
                  ),
      ),
    );
  }

  Widget _vacio() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 120, 24, 96),
      children: [
        const Icon(Icons.directions_car, size: 78, color: AppColors.slate500),
        const SizedBox(height: 16),
        const Text(
          'No tienes vehiculos registrados.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white, fontSize: 18),
        ),
        const SizedBox(height: 8),
        const Text(
          'Registra uno para que el diagnostico IA pueda crear una alerta.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.slate400),
        ),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: _abrirFormulario,
          icon: const Icon(Icons.add, color: Colors.white),
          label: const Text(
            'Registrar vehiculo',
            style: TextStyle(color: Colors.white),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.orange500,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ],
    );
  }
}

class _VehiculoCard extends StatelessWidget {
  const _VehiculoCard({required this.vehiculo});

  final dynamic vehiculo;

  @override
  Widget build(BuildContext context) {
    final activo = vehiculo['activo'] != false;

    return Card(
      color: AppColors.slate800,
      margin: const EdgeInsets.only(bottom: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.directions_car, color: AppColors.orange500),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '${vehiculo['marca'] ?? '-'} ${vehiculo['modelo'] ?? ''}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: (activo ? Colors.green : AppColors.red500)
                        .withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    activo ? 'Activo' : 'Inactivo',
                    style: TextStyle(
                      color: activo ? Colors.green : AppColors.red400,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _dato('Placa', vehiculo['placa'] ?? '-'),
            _dato('Anio', '${vehiculo['anio'] ?? 'N/A'}'),
            _dato('Color', vehiculo['color'] ?? 'N/A'),
            _dato('Tipo', vehiculo['tipo_vehiculo'] ?? 'N/A'),
          ],
        ),
      ),
    );
  }

  Widget _dato(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(
            width: 64,
            child: Text(
              label,
              style: const TextStyle(color: AppColors.slate400, fontSize: 12),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: Colors.white, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class VehiculoFormScreen extends StatefulWidget {
  const VehiculoFormScreen({Key? key}) : super(key: key);

  @override
  State<VehiculoFormScreen> createState() => _VehiculoFormScreenState();
}

class _VehiculoFormScreenState extends State<VehiculoFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _placaController = TextEditingController();
  final _marcaController = TextEditingController();
  final _modeloController = TextEditingController();
  final _anioController = TextEditingController();
  final _colorController = TextEditingController();
  final _tipoController = TextEditingController();
  final _vinController = TextEditingController();
  bool _guardando = false;

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _guardando = true);

    final data = <String, dynamic>{
      'placa': _placaController.text.trim().toUpperCase(),
      'marca': _marcaController.text.trim(),
      'modelo': _modeloController.text.trim(),
    };

    final anio = int.tryParse(_anioController.text.trim());
    if (anio != null) data['anio'] = anio;
    if (_colorController.text.trim().isNotEmpty) {
      data['color'] = _colorController.text.trim();
    }
    if (_tipoController.text.trim().isNotEmpty) {
      data['tipo_vehiculo'] = _tipoController.text.trim();
    }
    if (_vinController.text.trim().isNotEmpty) {
      data['vin'] = _vinController.text.trim();
    }

    try {
      await VehiculoService.registrarVehiculo(data);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vehiculo registrado correctamente.')),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudo registrar: $e')),
      );
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  void dispose() {
    _placaController.dispose();
    _marcaController.dispose();
    _modeloController.dispose();
    _anioController.dispose();
    _colorController.dispose();
    _tipoController.dispose();
    _vinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: AppBar(
        title: const Text('Registrar vehiculo'),
        backgroundColor: AppColors.slate800,
        elevation: 0,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _campo(
              controller: _placaController,
              label: 'Placa',
              icon: Icons.pin,
              isRequired: true,
              textCapitalization: TextCapitalization.characters,
            ),
            _campo(
              controller: _marcaController,
              label: 'Marca',
              icon: Icons.factory,
              isRequired: true,
            ),
            _campo(
              controller: _modeloController,
              label: 'Modelo',
              icon: Icons.directions_car,
              isRequired: true,
            ),
            _campo(
              controller: _anioController,
              label: 'Anio',
              icon: Icons.calendar_today,
              keyboardType: TextInputType.number,
            ),
            _campo(
              controller: _colorController,
              label: 'Color',
              icon: Icons.palette,
            ),
            _campo(
              controller: _tipoController,
              label: 'Tipo de vehiculo',
              icon: Icons.category,
            ),
            _campo(
              controller: _vinController,
              label: 'VIN',
              icon: Icons.confirmation_number,
              textCapitalization: TextCapitalization.characters,
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _guardando ? null : _guardar,
                icon: _guardando
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Icon(Icons.save, color: Colors.white),
                label: Text(
                  _guardando ? 'Guardando...' : 'Guardar vehiculo',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.orange500,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _campo({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool isRequired = false,
    TextInputType? keyboardType,
    TextCapitalization textCapitalization = TextCapitalization.words,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        textCapitalization: textCapitalization,
        style: const TextStyle(color: Colors.white),
        validator: isRequired
            ? (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Campo requerido';
                }
                return null;
              }
            : null,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: AppColors.slate400),
          prefixIcon: Icon(icon, color: AppColors.slate400),
          filled: true,
          fillColor: AppColors.slate800,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }
}
