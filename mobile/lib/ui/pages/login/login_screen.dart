import 'package:flutter/material.dart';
import '../../shared/colors.dart';
import '../../../core/services/auth_service.dart';
import '../../../core/services/push_notification_service.dart';
import '../dashboard/dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _showPassword = false;

  static const _demoAccounts = [
    ('ADMINISTRADOR', 'admin@emergencia.com', 'Admin1234', Icons.admin_panel_settings),
    ('TALLER', 'taller@emergencia.com', 'Taller1234', Icons.handyman_outlined),
    ('CLIENTE', 'cliente@emergencia.com', 'Cliente1234', Icons.person_outline),
  ];

  @override
  void initState() {
    super.initState();
    // Autocompletar como en el frontend
    _emailController.text = 'admin@emergencia.com';
    _passwordController.text = 'Admin1234';
  }

  void _useDemoAccount((String, String, String, IconData) account) {
    setState(() {
      _emailController.text = account.$2;
      _passwordController.text = account.$3;
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, ingresa correo y contraseña')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    final success = await AuthService.login(
      _emailController.text,
      _passwordController.text,
    );

    setState(() {
      _isLoading = false;
    });

    if (success) {
      await PushNotificationService.init();
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const DashboardScreen()),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Credenciales inválidas o error de conexión')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate900,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Logo O Brand centralizado
              Center(
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppColors.orange500,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.orange500.withOpacity(0.3),
                        blurRadius: 15,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.airport_shuttle, color: Colors.white, size: 32),
                ),
              ),
              const SizedBox(height: 24),
              const Center(
                child: Text(
                  'EmergenciaVehicular',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    letterSpacing: -0.5,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Center(
                child: Text(
                  'Bienvenido de nuevo',
                  style: TextStyle(
                    color: AppColors.slate400,
                    fontSize: 16,
                  ),
                ),
              ),
              const SizedBox(height: 48),

              // Contenedor del Formulario
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppColors.slate800,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppColors.slate400.withOpacity(0.1)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Accesos rápidos',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 10),
                    ..._demoAccounts.map((account) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: OutlinedButton.icon(
                            onPressed: _isLoading
                                ? null
                                : () => _useDemoAccount(account),
                            icon: Icon(account.$4, size: 18),
                            label: Text('${account.$1}  ·  ${account.$2}'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppColors.orange400,
                              side: BorderSide(
                                color: AppColors.orange500.withOpacity(0.45),
                              ),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 12,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        )),
                    const SizedBox(height: 12),
                    const Text('Correo Electrónico', style: TextStyle(color: AppColors.slate400, fontSize: 14)),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _emailController,
                      style: const TextStyle(color: Colors.white),
                      keyboardType: TextInputType.emailAddress,
                      decoration: InputDecoration(
                        hintText: 'ejemplo@correo.com',
                        hintStyle: TextStyle(color: AppColors.slate400.withOpacity(0.5)),
                        filled: true,
                        fillColor: AppColors.slate900.withOpacity(0.5),
                        prefixIcon: const Icon(Icons.email_outlined, color: AppColors.slate400),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    const Text('Contraseña', style: TextStyle(color: AppColors.slate400, fontSize: 14)),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _passwordController,
                      obscureText: !_showPassword,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: AppColors.slate900.withOpacity(0.5),
                        prefixIcon: const Icon(Icons.lock_outline, color: AppColors.slate400),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _showPassword ? Icons.visibility : Icons.visibility_off,
                            color: AppColors.slate400,
                          ),
                          onPressed: () {
                            setState(() {
                              _showPassword = !_showPassword;
                            });
                          },
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),

                    SizedBox(
                      height: 54,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _submit,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.orange500,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 0,
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : const Text(
                                'Ingresar',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Etiqueta Demo
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.orange500.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: AppColors.orange500,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Toca un rol para cargar sus credenciales',
                              style: TextStyle(
                                color: AppColors.orange400,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
