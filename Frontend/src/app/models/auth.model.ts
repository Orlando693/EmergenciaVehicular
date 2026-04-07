export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: string;
  id_usuario: number;
  nombre: string;
}

export interface TokenPayload {
  sub: string;
  email: string;
  roles: string[];
  exp: number;
}
