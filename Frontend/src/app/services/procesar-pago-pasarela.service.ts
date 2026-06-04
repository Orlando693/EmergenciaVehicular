import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface InfoPagoOut {
  id_incidente: number;
  estado_incidente: string;
  monto_total: number;
  monto_taller: number;
  comision_plataforma: number;
  cotizacion_aceptada_id: number | null;
  precio_cotizacion: number | null;
  pago_estado: string | null;
  pago_referencia: string | null;
}

export interface ProcesarPagoRequest {
  metodo_pago: string;             // TARJETA | TRANSFERENCIA | EFECTIVO
  numero_tarjeta?: string | null;
  nombre_titular?: string | null;
  vencimiento?: string | null;
  cvv?: string | null;
  gateway?: string;
}

export interface PagoGatewayTransaccionOut {
  id_transaccion: number;
  id_pago: number;
  gateway_nombre: string;
  metodo_pago: string;
  monto: number;
  intento_numero: number;
  gateway_referencia: string | null;
  gateway_codigo: string | null;
  gateway_mensaje: string | null;
  estado: string;
  created_at: string;
}

export interface ResultadoPagoOut {
  id_pago: number;
  id_incidente: number;
  estado_pago: string;
  referencia: string | null;
  monto_total: number;
  estado_incidente: string;
  transaccion: PagoGatewayTransaccionOut;
  mensaje: string;
}

@Injectable({ providedIn: 'root' })
export class ProcesarPagoPasarelaService {
  private apiUrl = `${environment.apiUrl}/procesar-pago`;

  constructor(private http: HttpClient) {}

  obtenerInfo(idIncidente: number): Observable<InfoPagoOut> {
    return this.http.get<InfoPagoOut>(`${this.apiUrl}/${idIncidente}`);
  }

  procesarPago(idIncidente: number, payload: ProcesarPagoRequest): Observable<ResultadoPagoOut> {
    return this.http.post<ResultadoPagoOut>(`${this.apiUrl}/${idIncidente}/procesar`, payload);
  }

  listarTransacciones(idIncidente: number): Observable<PagoGatewayTransaccionOut[]> {
    return this.http.get<PagoGatewayTransaccionOut[]>(`${this.apiUrl}/${idIncidente}/transacciones`);
  }
}
