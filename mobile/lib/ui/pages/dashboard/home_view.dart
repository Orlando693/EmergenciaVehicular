import 'package:flutter/material.dart';
import '../../../core/services/auth_service.dart';
import '../../shared/colors.dart';

class HomeView extends StatelessWidget {
  const HomeView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final user = AuthService.currentUser;
    final esCliente = user?.rol == 'CLIENTE';

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.home_repair_service,
              size: 80,
              color: AppColors.orange500,
            ),
            const SizedBox(height: 24),
            Text(
              'Bienvenido, ${user?.nombre ?? "Usuario"}',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.blue950,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.slate400.withValues(alpha: 0.3),
                ),
              ),
              child: Text(
                'Rol activo: ${user?.rol ?? "Desconocido"}',
                style: const TextStyle(color: AppColors.slate400),
              ),
            ),
            const SizedBox(height: 32),
            Text(
              esCliente
                  ? 'Usa el menu inferior o el sidebar para abrir Diagnostico IA, Chat y Notificaciones.'
                  : 'Navega desde el menu inferior para usar las opciones de tu plan.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.slate500, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}
