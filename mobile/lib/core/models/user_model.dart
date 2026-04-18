class UserModel {
  final int idUsuario;
  final String email;
  final String nombre;
  final String rol;
  final String accessToken;

  UserModel({
    required this.idUsuario,
    required this.email,
    required this.nombre,
    required this.rol,
    required this.accessToken,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      idUsuario: json['id_usuario'] ?? 0,
      email: json['email'] ?? '',
      nombre: json['nombre'] ?? '',
      rol: json['rol'] ?? '',
      accessToken: json['access_token'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_usuario': idUsuario,
      'email': email,
      'nombre': nombre,
      'rol': rol,
      'access_token': accessToken,
    };
  }
}