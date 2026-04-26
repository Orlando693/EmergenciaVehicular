import { Injectable, inject, signal, OnDestroy } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

export interface Notificacion {
  id_notificacion: number;
  id_usuario: number;
  id_incidente?: number;
  titulo: string;
  mensaje: string;
  tipo: string;
  leida: boolean;
  created_at: string;
}

export interface NotificacionPage {
  items: Notificacion[];
  total: number;
  no_leidas: number;
}

@Injectable({ providedIn: 'root' })
export class NotificacionesService implements OnDestroy {
  private http    = inject(HttpClient);
  private apiUrl  = `${environment.apiUrl}/notificaciones`;
  private wsUrl   = `${environment.wsUrl}/notificaciones/ws`;

  private ws: WebSocket | null = null;
  private reconnectTimer: any   = null;

  noLeidas     = signal(0);
  recientes    = signal<Notificacion[]>([]);

  // ── HTTP ────────────────────────────────────────────────────────

  listar(skip = 0, limit = 20): Observable<NotificacionPage> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<NotificacionPage>(this.apiUrl, { params });
  }

  contarNoLeidas(): Observable<{ count: number }> {
    return this.http.get<{ count: number }>(`${this.apiUrl}/no-leidas`);
  }

  marcarLeida(id: number): Observable<Notificacion> {
    return this.http.patch<Notificacion>(`${this.apiUrl}/${id}/leer`, {});
  }

  marcarTodasLeidas(): Observable<any> {
    return this.http.patch(`${this.apiUrl}/leer-todas`, {});
  }

  // ── WebSocket ───────────────────────────────────────────────────

  conectar(token: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${this.wsUrl}?token=${token}`);

    this.ws.onopen = () => {
      clearTimeout(this.reconnectTimer);
    };

    this.ws.onmessage = (event) => {
      try {
        const notif: Notificacion = JSON.parse(event.data);
        this.recientes.update(prev => [notif, ...prev].slice(0, 50));
        this.noLeidas.update(n => n + 1);
      } catch { /* ignore parse errors */ }
    };

    this.ws.onerror = () => { /* handled by onclose */ };

    this.ws.onclose = () => {
      // Reconectar tras 5s si aún hay token
      this.reconnectTimer = setTimeout(() => {
        if (token) this.conectar(token);
      }, 5000);
    };
  }

  desconectar() {
    clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.noLeidas.set(0);
    this.recientes.set([]);
  }

  ngOnDestroy() { this.desconectar(); }
}
