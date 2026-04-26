import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ResumenGeneral {
  total_incidentes:          number;
  incidentes_reportados:     number;
  incidentes_en_proceso:     number;
  incidentes_resueltos:      number;
  incidentes_pagados:        number;
  incidentes_cancelados:     number;
  total_usuarios:            number;
  total_clientes:            number;
  total_talleres:            number;
  total_pagos_completados:   number;
  ingresos_totales:          number;
  comision_plataforma_total: number;
}

export interface ItemIncidente {
  id_incidente:     number;
  clasificacion_ia: string | null;
  estado:           string;
  taller_nombre:    string | null;
  direccion:        string | null;
  created_at:       string;
}
export interface ReporteIncidentes { items: ItemIncidente[]; total: number; por_estado: Record<string, number>; }

export interface ItemUsuario {
  id_usuario: number; nombres: string; apellidos: string;
  email: string; rol: string; estado: string; created_at: string;
}
export interface ReporteUsuarios { items: ItemUsuario[]; total: number; por_rol: Record<string, number>; }

export interface ItemTaller {
  id_taller: number; razon_social: string; estado_registro: string;
  total_servicios: number; servicios_completados: number; ingresos_taller: number;
}
export interface ReporteTalleres { items: ItemTaller[]; total: number; total_ingresos: number; }

export interface ItemPago {
  id_pago: number; id_incidente: number; metodo_pago: string;
  monto_total: number; monto_taller: number; comision_plataforma: number;
  estado: string; referencia: string | null; created_at: string;
}
export interface ReportePagos {
  items: ItemPago[]; total: number; monto_total: number; comision_total: number;
  por_metodo: Record<string, number>; por_estado: Record<string, number>;
}

@Injectable({ providedIn: 'root' })
export class ReportesService {
  private http   = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/reportes`;

  resumen(): Observable<ResumenGeneral> {
    return this.http.get<ResumenGeneral>(`${this.apiUrl}/resumen`);
  }

  incidentes(f: { desde?: string; hasta?: string; estado?: string; idTaller?: number }): Observable<ReporteIncidentes> {
    let p = new HttpParams();
    if (f.desde)    p = p.set('desde',     f.desde);
    if (f.hasta)    p = p.set('hasta',     f.hasta);
    if (f.estado)   p = p.set('estado',    f.estado);
    if (f.idTaller) p = p.set('id_taller', f.idTaller);
    return this.http.get<ReporteIncidentes>(`${this.apiUrl}/incidentes`, { params: p });
  }

  usuarios(f: { desde?: string; hasta?: string; rol?: string }): Observable<ReporteUsuarios> {
    let p = new HttpParams();
    if (f.desde) p = p.set('desde', f.desde);
    if (f.hasta) p = p.set('hasta', f.hasta);
    if (f.rol)   p = p.set('rol',   f.rol);
    return this.http.get<ReporteUsuarios>(`${this.apiUrl}/usuarios`, { params: p });
  }

  talleres(): Observable<ReporteTalleres> {
    return this.http.get<ReporteTalleres>(`${this.apiUrl}/talleres`);
  }

  pagos(f: { desde?: string; hasta?: string; estado?: string; metodo?: string }): Observable<ReportePagos> {
    let p = new HttpParams();
    if (f.desde)  p = p.set('desde',  f.desde);
    if (f.hasta)  p = p.set('hasta',  f.hasta);
    if (f.estado) p = p.set('estado', f.estado);
    if (f.metodo) p = p.set('metodo', f.metodo);
    return this.http.get<ReportePagos>(`${this.apiUrl}/pagos`, { params: p });
  }
}
