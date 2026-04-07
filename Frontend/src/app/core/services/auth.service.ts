import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { LoginRequest, TokenResponse } from '../../models/auth.model';

const TOKEN_KEY = 'ev_token';
const SESSION_KEY = 'ev_session';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = environment.apiUrl;

  session = signal<TokenResponse | null>(this._loadSession());

  constructor(private http: HttpClient, private router: Router) {}

  login(credentials: LoginRequest) {
    return this.http.post<TokenResponse>(`${this.api}/auth/login`, credentials).pipe(
      tap(res => {
        localStorage.setItem(TOKEN_KEY, res.access_token);
        localStorage.setItem(SESSION_KEY, JSON.stringify(res));
        this.session.set(res);
      })
    );
  }

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
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

  private _loadSession(): TokenResponse | null {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
