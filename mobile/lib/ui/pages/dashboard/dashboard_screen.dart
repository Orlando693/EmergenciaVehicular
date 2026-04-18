import 'package:flutter/material.dart';
import '../../../core/services/auth_service.dart';
import '../../shared/colors.dart';
import '../login/login_screen.dart';
import 'home_view.dart';
import 'perfil_view.dart';
import 'usuarios_view.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  void _logout(BuildContext context) async {
    await AuthService.logout();
    if (context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = AuthService.currentUser;
    final isAdmin = user?.rol == 'ADMINISTRADOR';

    // Construimos dinámicamente las pestañas según el rol
    final List<Widget> pages = [
      const HomeView(),
      if (isAdmin) const UsuariosView(),
      const PerfilView(),
    ];

    final List<BottomNavigationBarItem> navItems = [
      const BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Inicio'),
      if (isAdmin) const BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Usuarios'),
      const BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Mi Perfil'),
    ];

    // Evitamos desbordes si el admin pasa a cliente en QA
    if (_currentIndex >= pages.length) {
      _currentIndex = 0;
    }

    return Scaffold(
      backgroundColor: AppColors.slate900,
      appBar: AppBar(
        backgroundColor: AppColors.slate800,
        elevation: 0,
        title: const Text('Panel de Control', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: AppColors.red500),
            onPressed: () => _logout(context),
            tooltip: 'Cerrar sesión',
          )
        ],
      ),
      body: pages[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppColors.slate800,
        selectedItemColor: AppColors.orange500,
        unselectedItemColor: AppColors.slate400,
        currentIndex: _currentIndex,
        type: BottomNavigationBarType.fixed,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: navItems,
      ),
    );
  }
}
