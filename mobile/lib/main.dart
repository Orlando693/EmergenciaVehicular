import 'package:flutter/material.dart';
import 'core/services/auth_service.dart';
import 'ui/pages/login/login_screen.dart';
import 'ui/pages/dashboard/dashboard_screen.dart';
import 'ui/shared/colors.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Intentar cargar la sesión si existe (ev_token en localStorage/SharedPreferences)
  final isLoggedIn = await AuthService.loadSession();

  runApp(MyApp(isLoggedIn: isLoggedIn));
}

class MyApp extends StatelessWidget {
  final bool isLoggedIn;

  const MyApp({Key? key, required this.isLoggedIn}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Emergencia Vehicular',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Montserrat',
        scaffoldBackgroundColor: AppColors.slate900,
        primaryColor: AppColors.orange500,
        colorScheme: ColorScheme.fromSwatch(
          primarySwatch: Colors.orange,
          brightness: Brightness.dark,
        ),
      ),
      home: isLoggedIn ? const DashboardScreen() : const LoginScreen(),
    );
  }
}
