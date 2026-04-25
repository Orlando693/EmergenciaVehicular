import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface IncidenteOut {
  id_incidente: number;
  id_cliente: number;
  id_vehiculo?: number;
  id_taller?: number;
  descripcion: string;
  audio_url?: string;
  imagen_url?: string;
  resumen_ia?: string;
  clasificacion_ia?: string;
  ubicacion_lat?: number;
  ubicacion_lng?: number;
  direccion?: string;
  estado: string;
  created_at: string;
  updated_at: string;
  taller_nombre?: string;
  vehiculo_placa?: string;
  vehiculo_marca?: string;
  vehiculo_modelo?: string;
}

export interface IncidenteCreate {
  id_vehiculo: number;
  descripcion: string;
  ubicacion_lat?: number;
  ubicacion_lng?: number;
  direccion?: string;
  audio_url?: string;
  imagen_url?: string;
}

export interface IncidenteEstadoUpdate {
  estado: string; // 'EN_PROCESO', 'RESUELTO', 'CANCELADO'
  observacion?: string;
}

export interface IncidenteHistorialOut {
  id_historial: number;
  id_incidente: number;
  estado_anterior?: string;
  estado_nuevo: string;
  observacion?: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class IncidenteService {
  private http = inject(HttpClient);
  
  private get apiUrl() {
    return `${environment.apiUrl}/incidentes`;
  }

  registrarIncidente(data: IncidenteCreate): Observable<IncidenteOut> {
    return this.http.post<IncidenteOut>(this.apiUrl, data);
  }

  consultarHistorial(): Observable<IncidenteOut[]> {
    return this.http.get<IncidenteOut[]>(this.apiUrl);
  }

  obtenerDetalle(id_incidente: number): Observable<IncidenteOut> {
    return this.http.get<IncidenteOut>(`${this.apiUrl}/${id_incidente}`);
  }

  asignarTaller(id_incidente: number): Observable<IncidenteOut> {
    return this.http.post<IncidenteOut>(`${this.apiUrl}/${id_incidente}/asignar-taller`, {});
  }

  actualizarEstado(id_incidente: number, data: IncidenteEstadoUpdate): Observable<IncidenteOut> {
    return this.http.patch<IncidenteOut>(`${this.apiUrl}/${id_incidente}/estado`, data);
  }

  consultarHistorialEstados(id_incidente: number): Observable<IncidenteHistorialOut[]> {
    return this.http.get<IncidenteHistorialOut[]>(`${this.apiUrl}/${id_incidente}/historial`);
  }
}
