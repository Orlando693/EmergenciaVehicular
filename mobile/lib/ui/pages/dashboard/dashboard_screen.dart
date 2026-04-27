import 'package:flutter/material.dart';
import '../../../core/services/auth_service.dart';
import '../../shared/colors.dart';
import '../incidentes/crear_incidente_screen.dart';
import '../incidentes/mis_alertas_screen.dart';
import '../login/login_screen.dart';
import '../vehiculos/mis_vehiculos_screen.dart';
import 'home_view.dart';
import 'notificaciones_view.dart';
import 'perfil_view.dart';
import 'usuarios_view.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  bool get _isCliente => AuthService.currentUser?.rol == 'CLIENTE';

  Future<void> _logout(BuildContext context) async {
    await AuthService.logout();
    if (!context.mounted) return;

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (context) => const LoginScreen()),
    );
  }

  Future<void> _abrirSos() async {
    final result = await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const CrearIncidenteScreen()),
    );

    if (result != null && mounted) {
      setState(() => _currentIndex = _isCliente ? 2 : 0);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = AuthService.currentUser;
    final isAdmin = user?.rol == 'ADMINISTRADOR';

    final pages = <Widget>[
      const HomeView(),
      if (_isCliente) const MisVehiculosScreen(showAppBar: false),
      if (_isCliente) const MisAlertasScreen(showAppBar: false),
      if (_isCliente) const NotificacionesView(),
      if (isAdmin) const UsuariosView(),
      const PerfilView(),
    ];

    final navItems = <BottomNavigationBarItem>[
      const BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Inicio'),
      if (_isCliente)
        const BottomNavigationBarItem(
          icon: Icon(Icons.directions_car),
          label: 'Vehiculos',
        ),
      if (_isCliente)
        const BottomNavigationBarItem(
          icon: Icon(Icons.chat_bubble_outline),
          label: 'Chat',
        ),
      if (_isCliente)
        const BottomNavigationBarItem(
          icon: Icon(Icons.notifications_none),
          label: 'Avisos',
        ),
      if (isAdmin)
        const BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Usuarios'),
      const BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Perfil'),
    ];

    if (_currentIndex >= pages.length) {
      _currentIndex = 0;
    }

    return Scaffold(
      backgroundColor: AppColors.slate900,
      drawer: _DashboardDrawer(
        selectedIndex: _currentIndex,
        isCliente: _isCliente,
        isAdmin: isAdmin,
        onSelect: (index) {
          Navigator.of(context).pop();
          setState(() => _currentIndex = index);
        },
        onSos: () {
          Navigator.of(context).pop();
          _abrirSos();
        },
        onLogout: () => _logout(context),
      ),
      appBar: AppBar(
        backgroundColor: AppColors.slate800,
        elevation: 0,
        title: const Text(
          'Emergencia Vehicular',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          if (_isCliente)
            IconButton(
              icon: const Icon(Icons.psychology_alt, color: Colors.white),
              tooltip: 'Diagnostico IA',
              onPressed: _abrirSos,
            ),
          if (_isCliente)
            IconButton(
              icon: const Icon(Icons.notifications_none, color: Colors.white),
              tooltip: 'Notificaciones',
              onPressed: () => setState(() => _currentIndex = 3),
            ),
          IconButton(
            icon: const Icon(Icons.logout, color: AppColors.red500),
            onPressed: () => _logout(context),
            tooltip: 'Cerrar sesion',
          ),
        ],
      ),
      body: pages[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppColors.slate800,
        selectedItemColor: AppColors.orange500,
        unselectedItemColor: AppColors.slate400,
        currentIndex: _currentIndex,
        type: BottomNavigationBarType.fixed,
        onTap: (index) => setState(() => _currentIndex = index),
        items: navItems,
      ),
    );
  }
}

class _DashboardDrawer extends StatelessWidget {
  const _DashboardDrawer({
    required this.selectedIndex,
    required this.isCliente,
    required this.isAdmin,
    required this.onSelect,
    required this.onSos,
    required this.onLogout,
  });

  final int selectedIndex;
  final bool isCliente;
  final bool isAdmin;
  final ValueChanged<int> onSelect;
  final VoidCallback onSos;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    final user = AuthService.currentUser;
    var perfilIndex = 1;
    if (isCliente) perfilIndex = 4;
    if (isAdmin) perfilIndex = 2;

    return Drawer(
      backgroundColor: AppColors.slate900,
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  const CircleAvatar(
                    radius: 24,
                    backgroundColor: AppColors.orange500,
                    child: Icon(Icons.person, color: Colors.white),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.nombre ?? 'Usuario',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          user?.rol ?? 'Sin rol',
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
            ),
            const Divider(color: AppColors.slate700, height: 1),
            _drawerItem(
              icon: Icons.home,
              label: 'Inicio',
              index: 0,
              onTap: () => onSelect(0),
            ),
            if (isCliente) ...[
              _drawerItem(
                icon: Icons.emergency_share,
                label: 'Diagnostico IA',
                index: -1,
                onTap: onSos,
              ),
              _drawerItem(
                icon: Icons.directions_car,
                label: 'Mis vehiculos',
                index: 1,
                onTap: () => onSelect(1),
              ),
              _drawerItem(
                icon: Icons.chat_bubble_outline,
                label: 'Alertas y chat',
                index: 2,
                onTap: () => onSelect(2),
              ),
              _drawerItem(
                icon: Icons.notifications_none,
                label: 'Notificaciones',
                index: 3,
                onTap: () => onSelect(3),
              ),
            ],
            if (isAdmin)
              _drawerItem(
                icon: Icons.group,
                label: 'Usuarios',
                index: 1,
                onTap: () => onSelect(1),
              ),
            _drawerItem(
              icon: Icons.person,
              label: 'Mi perfil',
              index: perfilIndex,
              onTap: () => onSelect(perfilIndex),
            ),
            const Spacer(),
            const Divider(color: AppColors.slate700, height: 1),
            ListTile(
              leading: const Icon(Icons.logout, color: AppColors.red500),
              title: const Text(
                'Cerrar sesion',
                style: TextStyle(color: Colors.white),
              ),
              onTap: onLogout,
            ),
          ],
        ),
      ),
    );
  }

  Widget _drawerItem({
    required IconData icon,
    required String label,
    required int index,
    required VoidCallback onTap,
  }) {
    final selected = selectedIndex == index;

    return ListTile(
      selected: selected,
      selectedTileColor: AppColors.orange500.withValues(alpha: 0.12),
      leading: Icon(
        icon,
        color: selected ? AppColors.orange500 : AppColors.slate400,
      ),
      title: Text(
        label,
        style: TextStyle(
          color: selected ? AppColors.orange500 : Colors.white,
          fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      onTap: onTap,
    );
  }
}
