import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { LoginRequest, TokenResponse } from '../../models/auth.model';

const TOKEN_KEY = 'ev_token';
const SESSION_KEY = 'ev_session';
const TENANT_ID_KEY = 'ev_id_tenant';
const TENANT_NAME_KEY = 'ev_tenant_nombre';
const TENANT_SLUG_KEY = 'ev_tenant_slug';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = environment.apiUrl;

  session = signal<TokenResponse | null>(this._loadSession());

  constructor(private http: HttpClient, private router: Router) {}

  login(credentials: LoginRequest) {
    console.log(credentials);
    return this.http.post<TokenResponse>(`${this.api}/auth/login`, credentials).pipe(
      tap(res => {
        console.log(res);
        localStorage.setItem(TOKEN_KEY, res.access_token);
        localStorage.setItem(SESSION_KEY, JSON.stringify(res));
        if (res.id_tenant != null) localStorage.setItem(TENANT_ID_KEY, String(res.id_tenant));
        if (res.tenant_nombre) localStorage.setItem(TENANT_NAME_KEY, res.tenant_nombre);
        if (res.tenant_slug) localStorage.setItem(TENANT_SLUG_KEY, res.tenant_slug);
        this.session.set(res);
      })
    );
  }

  logout() {
    // Limpiar cola offline del tenant actual antes de cerrar sesión
    const tenantId = this.idTenant;
    if (tenantId) {
      localStorage.removeItem(`emergencias_offline_${tenantId}`);
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(TENANT_ID_KEY);
    localStorage.removeItem(TENANT_NAME_KEY);
    localStorage.removeItem(TENANT_SLUG_KEY);
    this.session.set(null);
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  get rol(): string {
    return this.session()?.rol ?? '';
  }

  get nombreCompleto(): string {
    return this.session()?.nombre ?? '';
  }

  get idUsuario(): number {
    return this.session()?.id_usuario ?? 0;
  }

  get idTenant(): number {
    return this.session()?.id_tenant ?? Number(localStorage.getItem(TENANT_ID_KEY) || 0);
  }

  get tenantNombre(): string {
    return this.session()?.tenant_nombre ?? localStorage.getItem(TENANT_NAME_KEY) ?? '';
  }

  get tenantSlug(): string {
    return this.session()?.tenant_slug ?? localStorage.getItem(TENANT_SLUG_KEY) ?? '';
  }

  private _loadSession(): TokenResponse | null {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
