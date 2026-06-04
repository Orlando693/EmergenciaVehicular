import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CotizacionComparacionOut {
  id_cotizacion: number;
  id_incidente: number;
  id_taller: number;
  taller_nombre: string | null;
  taller_direccion: string | null;
  taller_calificacion: number | null;
  taller_acepta_remolque: boolean;
  descripcion_solicitud: string | null;
  precio_estimado: number | null;
  detalle_danio: string | null;
  condiciones_servicio: string | null;
  tiempo_estimado: string | null;
  estado: string;
  respuesta_at: string | null;
  created_at: string;
}

export interface SeleccionTallerRequest {
  id_cotizacion: number;
}

export interface SeleccionTallerOut {
  id_incidente: number;
  id_taller: number;
  id_cotizacion_aceptada: number;
  taller_nombre: string | null;
  taller_direccion: string | null;
  estado_incidente: string;
  cotizaciones_rechazadas: number;
  mensaje: string;
}

@Injectable({ providedIn: 'root' })
export class SeleccionarTallerService {
  private apiUrl = `${environment.apiUrl}/seleccionar-taller`;

  constructor(private http: HttpClient) {}

  listarCotizaciones(idIncidente: number): Observable<CotizacionComparacionOut[]> {
    return this.http.get<CotizacionComparacionOut[]>(`${this.apiUrl}/${idIncidente}/cotizaciones`);
  }

  seleccionarTaller(idIncidente: number, payload: SeleccionTallerRequest): Observable<SeleccionTallerOut> {
    return this.http.post<SeleccionTallerOut>(`${this.apiUrl}/${idIncidente}/seleccionar`, payload);
  }

  obtenerSeleccionActual(idIncidente: number): Observable<SeleccionTallerOut | null> {
    return this.http.get<SeleccionTallerOut | null>(`${this.apiUrl}/${idIncidente}/seleccion`);
  }
}
