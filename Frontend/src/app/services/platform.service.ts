import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { PlatformAuthService } from '../core/services/platform-auth.service';

export interface TenantPlatform {
  id_tenant:   number;
  nombre:      string;
  slug:        string;
  estado:      string;
  plan_nombre: string | null;
  plan_slug:   string | null;
  created_at:  string;
}

export interface PlanPlatform {
  id_plan:                   number;
  slug:                      string;
  nombre:                    string;
  descripcion:               string | null;
  precio:                    number;
  max_incidentes_mes:        number;
  max_tecnicos:              number;
  max_usuarios:              number;
  tiene_ia:                  boolean;
  tiene_reportes_avanzados:  boolean;
  tiene_soporte_prioritario: boolean;
  tiene_notificaciones_push: boolean;
  estado:                    string;
  orden:                     number;
}

export interface TenantCreate {
  nombre:  string;
  slug:    string;
  id_plan?: number;
}

export interface PlanCreate {
  slug:                       string;
  nombre:                     string;
  descripcion:                string;
  precio:                     number;
  max_incidentes_mes:         number;
  max_tecnicos:               number;
  max_usuarios:               number;
  tiene_ia:                   boolean;
  tiene_reportes_avanzados:   boolean;
  tiene_soporte_prioritario:  boolean;
  tiene_notificaciones_push:  boolean;
  orden:                      number;
}

export interface ReportePredictivo {
  modelo: string;
  modo: string;
  registros_entrenamiento: number;
  total_organizaciones: number;
  prediccion_total_proximo_mes: number;
  organizaciones_riesgo_alto: number;
  historico_global: { periodo: string; incidentes: number }[];
  importancia_variables: { nombre: string; porcentaje: number }[];
  predicciones: {
    id_tenant: number;
    nombre: string;
    plan_nombre: string;
    incidentes_mes_actual: number;
    prediccion_proximo_mes: number;
    crecimiento_pct: number;
    riesgo: 'ALTO' | 'MEDIO' | 'BAJO';
    recomendacion: string;
  }[];
}

@Injectable({ providedIn: 'root' })
export class PlatformService {
  private readonly base = `${environment.apiUrl}/platform`;

  constructor(private http: HttpClient, private auth: PlatformAuthService) {}

  private get headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  // ── Tenants ──────────────────────────────────────────────────────────────

  getTenants() {
    return this.http.get<TenantPlatform[]>(`${this.base}/tenants`, { headers: this.headers });
  }

  crearTenant(data: TenantCreate) {
    return this.http.post<TenantPlatform>(`${this.base}/tenants`, data, { headers: this.headers });
  }

  cambiarEstadoTenant(id: number, estado: 'ACTIVO' | 'SUSPENDIDO') {
    return this.http.patch<TenantPlatform>(
      `${this.base}/tenants/${id}/estado`,
      { estado },
      { headers: this.headers }
    );
  }

  asignarPlan(id_tenant: number, id_plan: number) {
    return this.http.patch(
      `${this.base}/tenants/${id_tenant}/plan`,
      { id_plan },
      { headers: this.headers }
    );
  }

  // ── Planes ────────────────────────────────────────────────────────────────

  getPlanes() {
    return this.http.get<PlanPlatform[]>(`${this.base}/planes`, { headers: this.headers });
  }

  crearPlan(data: PlanCreate) {
    return this.http.post<PlanPlatform>(`${this.base}/planes`, data, { headers: this.headers });
  }

  editarPlan(id: number, data: PlanCreate) {
    return this.http.put<PlanPlatform>(`${this.base}/planes/${id}`, data, { headers: this.headers });
  }

  getReportePredictivo() {
    return this.http.get<ReportePredictivo>(`${this.base}/reportes/predictivos`, { headers: this.headers });
  }
}
