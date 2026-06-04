export interface LoginRequest {
  email: string;
  password: string;
  tenant_slug?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: string;
  id_usuario: number;
  nombre: string;
  id_tenant?: number;
  tenant_nombre?: string | null;
  tenant_slug?: string | null;
}

export interface TokenPayload {
  sub: string;
  email: string;
  roles: string[];
  id_tenant?: number;
  exp: number;
}
