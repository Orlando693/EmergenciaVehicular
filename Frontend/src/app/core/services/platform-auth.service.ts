import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface PlatformSession {
  access_token: string;
  token_type:   string;
  nombre:       string;
  email:        string;
  rol:          string;
}

const PLATFORM_TOKEN_KEY   = 'ev_platform_token';
const PLATFORM_SESSION_KEY = 'ev_platform_session';

@Injectable({ providedIn: 'root' })
export class PlatformAuthService {
  private readonly api = environment.apiUrl;

  session = signal<PlatformSession | null>(this._load());

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string) {
    return this.http
      .post<PlatformSession>(`${this.api}/platform/auth/login`, { email, password })
      .pipe(
        tap(res => {
          localStorage.setItem(PLATFORM_TOKEN_KEY, res.access_token);
          localStorage.setItem(PLATFORM_SESSION_KEY, JSON.stringify(res));
          this.session.set(res);
        })
      );
  }

  logout() {
    localStorage.removeItem(PLATFORM_TOKEN_KEY);
    localStorage.removeItem(PLATFORM_SESSION_KEY);
    this.session.set(null);
    this.router.navigate(['/platform/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(PLATFORM_TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  get nombre(): string {
    return this.session()?.nombre ?? '';
  }

  get email(): string {
    return this.session()?.email ?? '';
  }

  private _load(): PlatformSession | null {
    try {
      const raw = localStorage.getItem(PLATFORM_SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
