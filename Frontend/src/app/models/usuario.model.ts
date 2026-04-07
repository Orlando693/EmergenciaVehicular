export interface Usuario {
  id_usuario: number;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string | null;
  estado: 'ACTIVO' | 'INACTIVO' | 'BLOQUEADO';
  ultimo_acceso: string | null;
  created_at: string;
  roles: string[];
}

export interface UsuarioCreate {
  nombres: string;
  apellidos: string;
  email: string;
  password: string;
  telefono?: string;
  rol: string;
}

export interface UsuarioUpdate {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
}
