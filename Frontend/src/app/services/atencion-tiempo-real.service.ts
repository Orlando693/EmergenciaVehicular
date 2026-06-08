import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { IncidenteHistorialOut, IncidenteOut } from '../core/services/incidente.service';

export interface TallerSeguimiento {
  id_taller: number;
  razon_social: string;
  nombre_comercial?: string;
  telefono_atencion?: string;
  latitud?: number;
  longitud?: number;
}

export interface UbicacionTecnico {
  id_incidente: number;
  id_usuario: number;
  lat: number;
  lng: number;
  precision?: number;
  velocidad?: number;
  rumbo?: number;
  updated_at: string;
}

export interface AtencionSeguimientoOut {
  incidente: IncidenteOut;
  taller?: TallerSeguimiento | null;
  ubicacion_tecnico?: UbicacionTecnico | null;
  historial: IncidenteHistorialOut[];
  participantes_en_linea: number;
}

export interface AtencionEventoOut {
  tipo: string;
  id_incidente: number;
  estado: string;
  observacion?: string;
  created_at: string;
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

  enviarUbicacion(idIncidente: number, data: {
    lat: number;
    lng: number;
    precision?: number | null;
    velocidad?: number | null;
    rumbo?: number | null;
  }): Observable<UbicacionTecnico> {
    return this.http.post<UbicacionTecnico>(`${this.apiUrl}/${idIncidente}/ubicacion`, data);
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
