import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PlanOut {
  id_plan: number;
  slug: string;
  nombre: string;
  descripcion: string | null;
  precio: number;
  moneda: string;
  max_incidentes_mes: number;
  max_tecnicos: number;
  max_usuarios: number;
  tiene_ia: boolean;
  tiene_reportes_avanzados: boolean;
  tiene_soporte_prioritario: boolean;
  tiene_notificaciones_push: boolean;
  orden: number;
  estado: string;
}

export interface SuscripcionOut {
  id_suscripcion: number;
  id_tenant: number;
  id_plan: number;
  estado: string;
  es_trial: boolean;
  fecha_inicio: string;
  fecha_fin: string | null;
  plan: PlanOut;
}

@Injectable({ providedIn: 'root' })
export class PlanesService {
  private api = `${environment.apiUrl}/planes`;

  constructor(private http: HttpClient) {}

  listarPlanes(): Observable<PlanOut[]> {
    return this.http.get<PlanOut[]>(this.api);
  }

  miSuscripcion(): Observable<SuscripcionOut | null> {
    return this.http.get<SuscripcionOut | null>(`${this.api}/mi-suscripcion`);
  }

  suscribir(id_plan: number): Observable<SuscripcionOut> {
    return this.http.post<SuscripcionOut>(`${this.api}/suscribir`, { id_plan });
  }

  historial(): Observable<SuscripcionOut[]> {
    return this.http.get<SuscripcionOut[]>(`${this.api}/historial`);
  }
}
