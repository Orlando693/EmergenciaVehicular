import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface MensajeChat {
  id_mensaje:    number;
  id_incidente:  number;
  id_usuario?:   number;
  contenido:     string;
  nombre_emisor: string;
  rol_emisor:    string;
  created_at:    string;
}

export interface ChatHistorial {
  mensajes:  MensajeChat[];
  total:     number;
  en_linea:  number;
}

export interface MensajeWS {
  tipo:          'mensaje' | 'sistema';
  id_mensaje?:   number;
  id_usuario?:   number;
  nombre_emisor?: string;
  rol_emisor?:   string;
  contenido:     string;
  created_at:    string;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private http   = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/chat`;
  private wsBase = `${environment.wsUrl}/chat`;

  private ws: WebSocket | null = null;
  private reconnectTimer: any  = null;

  // ── HTTP ──────────────────────────────────────────────────────────

  obtenerHistorial(idIncidente: number, skip = 0, limit = 100): Observable<ChatHistorial> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<ChatHistorial>(`${this.apiUrl}/${idIncidente}`, { params });
  }

  // ── WebSocket ──────────────────────────────────────────────────────

  conectar(
    idIncidente: number,
    token: string,
    onMessage: (msg: MensajeWS) => void,
    onOpen?: () => void,
    onClose?: () => void,
  ): WebSocket {
    this.desconectar();
    const url = `${this.wsBase}/${idIncidente}/ws?token=${token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen  = () => { clearTimeout(this.reconnectTimer); onOpen?.(); };
    this.ws.onclose = () => { onClose?.(); };
    this.ws.onerror = () => { /* handled by onclose */ };
    this.ws.onmessage = (event) => {
      try { onMessage(JSON.parse(event.data)); } catch { /* skip */ }
    };

    return this.ws;
  }

  enviar(contenido: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ contenido }));
    }
  }

  desconectar() {
    clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
