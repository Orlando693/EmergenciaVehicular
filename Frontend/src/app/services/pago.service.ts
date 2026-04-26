import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CostoEstimado {
  id_incidente:        number;
  clasificacion_ia:    string | null;
  monto_total:         number;
  monto_taller:        number;
  comision_plataforma: number;
  pago_existente:      PagoOut | null;
}

export interface InfoPago {
  id_incidente:        number;
  clasificacion_ia:    string | null;
  estado_incidente?:   string | null;
  monto_total:         number;
  monto_taller:        number;
  comision_plataforma: number;
  pago_existente:      PagoOut | null;
}

export interface PagoOut {
  id_pago:             number;
  id_incidente:        number;
  id_cliente:          number;
  monto_total:         number;
  monto_taller:        number;
  comision_plataforma: number;
  metodo_pago:         string;
  estado:              string;
  referencia?:         string;
  descripcion_error?:  string;
  created_at:          string;
  updated_at:          string;
}

export interface PagoPage {
  items: PagoOut[];
  total: number;
}

export interface IniciarPagoRequest {
  metodo_pago:     string;
  numero_tarjeta?: string;
  nombre_titular?: string;
  vencimiento?:    string;
  cvv?:            string;
}

@Injectable({ providedIn: 'root' })
export class PagoService {
  private http   = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/pagos`;

  obtenerCosto(idIncidente: number): Observable<CostoEstimado> {
    return this.http.get<CostoEstimado>(`${this.apiUrl}/incidente/${idIncidente}/costo`);
  }

  /** A2 - Info de pago accesible para CLIENTE dueño, TALLER asignado o ADMIN. */
  infoPago(idIncidente: number): Observable<InfoPago> {
    return this.http.get<InfoPago>(`${this.apiUrl}/incidente/${idIncidente}/info`);
  }

  realizarPago(idIncidente: number, data: IniciarPagoRequest): Observable<PagoOut> {
    return this.http.post<PagoOut>(`${this.apiUrl}/incidente/${idIncidente}/pagar`, data);
  }

  misPagos(skip = 0, limit = 20): Observable<PagoPage> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<PagoPage>(`${this.apiUrl}/mis-pagos`, { params });
  }

  todosPagos(skip = 0, limit = 50): Observable<PagoPage> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<PagoPage>(`${this.apiUrl}/admin/todos`, { params });
  }
}
