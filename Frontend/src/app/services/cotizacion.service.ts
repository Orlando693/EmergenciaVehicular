import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CotizacionReparacionOut {
  id_cotizacion: number;
  id_incidente: number;
  id_cliente: number;
  id_taller: number;
  descripcion_solicitud?: string;
  estado: string;
  precio_estimado?: number;
  detalle_danio?: string;
  condiciones_servicio?: string;
  tiempo_estimado?: string;
  respuesta_at?: string;
  created_at: string;
  updated_at: string;
  taller_nombre?: string;
  incidente_estado?: string;
}

export interface CotizacionSolicitudCreate {
  id_incidente: number;
  descripcion_solicitud?: string;
}

export interface CotizacionRespuestaUpdate {
  precio_estimado: number;
  detalle_danio: string;
  condiciones_servicio: string;
  tiempo_estimado: string;
}

@Injectable({
  providedIn: 'root'
})
export class CotizacionService {
  private apiUrl = `${environment.apiUrl}/cotizaciones`;

  constructor(private http: HttpClient) {}

  solicitarCotizacion(payload: CotizacionSolicitudCreate): Observable<CotizacionReparacionOut> {
    return this.http.post<CotizacionReparacionOut>(`${this.apiUrl}/solicitar`, payload);
  }

  listarCotizaciones(): Observable<CotizacionReparacionOut[]> {
    return this.http.get<CotizacionReparacionOut[]>(this.apiUrl);
  }

  obtenerCotizacion(idCotizacion: number): Observable<CotizacionReparacionOut> {
    return this.http.get<CotizacionReparacionOut>(`${this.apiUrl}/${idCotizacion}`);
  }

  responderCotizacion(idCotizacion: number, payload: CotizacionRespuestaUpdate): Observable<CotizacionReparacionOut> {
    return this.http.patch<CotizacionReparacionOut>(`${this.apiUrl}/${idCotizacion}/responder`, payload);
  }
}
