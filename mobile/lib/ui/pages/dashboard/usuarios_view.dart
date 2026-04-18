import 'package:flutter/material.dart';
import '../../../core/services/usuario_service.dart';
import '../../shared/colors.dart';

class UsuariosView extends StatefulWidget {
  const UsuariosView({Key? key}) : super(key: key);

  @override
  State<UsuariosView> createState() => _UsuariosViewState();
}

class _UsuariosViewState extends State<UsuariosView> {
  List<dynamic> _usuarios = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _cargarUsuarios();
  }

  Future<void> _cargarUsuarios() async {
    setState(() => _isLoading = true);
    final data = await UsuarioService.listarUsuarios();
    setState(() {
      _usuarios = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.orange500));
    }

    if (_usuarios.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.group_off, size: 64, color: AppColors.slate600),
            const SizedBox(height: 16),
            const Text(
              'No se encontraron usuarios o hubo un error',
              style: TextStyle(color: AppColors.slate400),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.orange500),
              onPressed: _cargarUsuarios,
            )
          ],
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.orange500,
      backgroundColor: AppColors.slate800,
      onRefresh: _cargarUsuarios,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        itemCount: _usuarios.length,
        itemBuilder: (context, index) {
          final u = _usuarios[index];
          final estado = u['estado'] ?? '';
          final colorEstado = estado == 'ACTIVO' ? Colors.greenAccent : AppColors.red400;

          return Card(
            color: AppColors.slate800,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: AppColors.blue600,
                child: Text(
                  u['nombre']?.substring(0, 1)?.toUpperCase() ?? 'U',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              title: Text(
                u['nombre'] ?? 'Sin nombre',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
              subtitle: Text(
                '${u['email']}\nRol: ${u['rol'] ?? 'S/R'}',
                style: const TextStyle(color: AppColors.slate400),
              ),
              isThreeLine: true,
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.circle, size: 12, color: colorEstado),
                  const SizedBox(height: 4),
                  Text(
                    estado,
                    style: TextStyle(color: colorEstado, fontSize: 10, fontWeight: FontWeight.bold),
                  )
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
