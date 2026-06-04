import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TallerSeguimiento {
  id_taller: number;
  razon_social: string;
  telefono?: string;
  latitud?: number;
  longitud?: number;
}

export interface AtencionSeguimientoOut {
  id_incidente: number;
  descripcion: string;
  estado: string;
  latitud?: number;
  longitud?: number;
  taller_asignado?: TallerSeguimiento;
  eventos_recientes: AtencionEventoOut[];
}

export interface AtencionEventoOut {
  id_historial: number;
  id_incidente: number;
  nuevo_estado: string;
  observacion?: string;
  creado_en: string;
}

@Injectable({
  providedIn: 'root'
})
export class AtencionTiempoRealService {
  private apiUrl = `${environment.apiUrl}/atencion-tiempo-real`;
  private wsUrl = `${environment.wsUrl}/atencion-tiempo-real`;
  private ws: WebSocket | null = null;
  public eventos$ = new Subject<any>();

  constructor(private http: HttpClient) {}

  obtenerSeguimiento(idIncidente: number): Observable<AtencionSeguimientoOut> {
    return this.http.get<AtencionSeguimientoOut>(`${this.apiUrl}/${idIncidente}`);
  }

  aceptarAtencion(idIncidente: number, observacion?: string): Observable<AtencionEventoOut> {
    return this.http.post<AtencionEventoOut>(`${this.apiUrl}/${idIncidente}/aceptar`, { observacion });
  }

  rechazarAtencion(idIncidente: number, observacion?: string): Observable<AtencionEventoOut> {
    return this.http.post<AtencionEventoOut>(`${this.apiUrl}/${idIncidente}/rechazar`, { observacion });
  }

  actualizarEstado(idIncidente: number, estado: string, observacion?: string): Observable<AtencionEventoOut> {
    return this.http.patch<AtencionEventoOut>(`${this.apiUrl}/${idIncidente}/estado`, { estado, observacion });
  }

  conectarWebSocket(idIncidente: number, token: string): void {
    if (this.ws) {
      this.desconectarWebSocket();
    }
    
    this.ws = new WebSocket(`${this.wsUrl}/${idIncidente}/ws?token=${token}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.eventos$.next(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket cerrado');
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  desconectarWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}