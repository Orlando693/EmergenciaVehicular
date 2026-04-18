import 'package:flutter/material.dart';
import '../../../core/services/usuario_service.dart';
import '../../shared/colors.dart';

class PerfilView extends StatefulWidget {
  const PerfilView({Key? key}) : super(key: key);

  @override
  State<PerfilView> createState() => _PerfilViewState();
}

class _PerfilViewState extends State<PerfilView> {
  Map<String, dynamic>? _perfil;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _cargarPerfil();
  }

  Future<void> _cargarPerfil() async {
    setState(() => _isLoading = true);
    final data = await UsuarioService.miPerfil();
    setState(() {
      _perfil = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.orange500));
    }

    if (_perfil == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: AppColors.slate600),
            const SizedBox(height: 16),
            const Text('Error al cargar tu perfil', style: TextStyle(color: AppColors.slate400)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.orange500),
              onPressed: _cargarPerfil,
            )
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const CircleAvatar(
            radius: 50,
            backgroundColor: AppColors.blue600,
            child: Icon(Icons.person, size: 50, color: Colors.white),
          ),
          const SizedBox(height: 24),
          const Text(
            'Información Personal',
            style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          _buildInfoTile(Icons.badge, 'Nombre Completo', _perfil!['nombre'] ?? '-'),
          _buildInfoTile(Icons.email, 'Correo Electrónico', _perfil!['email'] ?? '-'),
          _buildInfoTile(Icons.security, 'Rol en el sistema', _perfil!['rol'] ?? '-'),
          _buildInfoTile(Icons.phone, 'Teléfono', _perfil!['telefono'] ?? 'No registrado'),
          _buildInfoTile(
            Icons.verified_user,
            'Estado de Cuenta',
            _perfil!['estado'] ?? '-',
            color: _perfil!['estado'] == 'ACTIVO' ? Colors.green : AppColors.red400,
          ),
        ],
      ),
    );
  }

  Widget _buildInfoTile(IconData icon, String title, String value, {Color? color}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.slate800,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.slate700),
      ),
      child: Row(
        children: [
          Icon(icon, color: color ?? AppColors.orange400, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: AppColors.slate400, fontSize: 12)),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    color: color ?? Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}
