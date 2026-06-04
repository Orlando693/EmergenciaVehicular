import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface EstimacionAtencionCreate {
  tiempo_llegada?: string | null;
  tiempo_reparacion?: string | null;
  observacion?: string | null;
}

export interface EstimacionAtencionUpdate {
  tiempo_llegada?: string | null;
  tiempo_reparacion?: string | null;
  observacion?: string | null;
}

export interface EstimacionAtencionOut {
  id_estimacion: number;
  id_incidente: number;
  id_taller: number;
  tiempo_llegada: string | null;
  tiempo_reparacion: string | null;
  observacion: string | null;
  taller_nombre: string | null;
  created_at: string;
  updated_at: string;
}

@Injectable({ providedIn: 'root' })
export class GestionarAtencionReparacionService {
  private apiUrl = `${environment.apiUrl}/gestionar-atencion`;

  constructor(private http: HttpClient) {}

  obtenerEstimacion(idIncidente: number): Observable<EstimacionAtencionOut> {
    return this.http.get<EstimacionAtencionOut>(`${this.apiUrl}/${idIncidente}/estimacion`);
  }

  registrarEstimacion(idIncidente: number, data: EstimacionAtencionCreate): Observable<EstimacionAtencionOut> {
    return this.http.post<EstimacionAtencionOut>(`${this.apiUrl}/${idIncidente}/estimacion`, data);
  }

  actualizarEstimacion(idIncidente: number, data: EstimacionAtencionUpdate): Observable<EstimacionAtencionOut> {
    return this.http.patch<EstimacionAtencionOut>(`${this.apiUrl}/${idIncidente}/estimacion`, data);
  }
}
