import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

interface KpiData {
  total_incidentes:         number;
  incidentes_activos:       number;
  incidentes_completados:   number;
  incidentes_cancelados:    number;
  total_talleres:           number;
  total_tecnicos:           number;
  total_clientes:           number;
  ingresos_totales:         number;
  cumplimiento_sla:         number;
  por_estado:               { nombre: string; total: number }[];
  por_clasificacion:        { nombre: string; total: number }[];
  por_taller:               { nombre: string; total_incidentes: number; completados: number; cancelados: number; tasa_cumplimiento: number }[];
  tendencia_7dias:          { fecha: string; total: number }[];
}

@Component({
  selector: 'app-dashboard-operacional',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard-operacional.component.html',
  styleUrls: ['./dashboard-operacional.component.css'],
})
export class DashboardOperacionalComponent implements OnInit {
  private api = `${environment.apiUrl}/dashboard-operacional`;

  data    = signal<KpiData | null>(null);
  loading = signal(true);
  error   = signal('');

  // Filtros
  fechaDesde = '';
  fechaHasta = '';
  clasificacion = '';

  // Barra más alta para escalar gráficas
  maxTendencia = computed(() => {
    const d = this.data();
    if (!d || d.tendencia_7dias.length === 0) return 1;
    return Math.max(...d.tendencia_7dias.map(t => t.total), 1);
  });

  maxClasificacion = computed(() => {
    const d = this.data();
    if (!d || d.por_clasificacion.length === 0) return 1;
    return Math.max(...d.por_clasificacion.map(c => c.total), 1);
  });

  diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

  constructor(private http: HttpClient, public auth: AuthService) {}

  ngOnInit() {
    this.cargar();
  }

  private get headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  cargar() {
    this.loading.set(true);
    this.error.set('');

    let params = new HttpParams();
    if (this.fechaDesde) params = params.set('fecha_desde', new Date(this.fechaDesde).toISOString());
    if (this.fechaHasta) params = params.set('fecha_hasta', new Date(this.fechaHasta).toISOString());
    if (this.clasificacion) params = params.set('clasificacion', this.clasificacion);

    this.http.get<KpiData>(this.api, { headers: this.headers, params }).subscribe({
      next: d => { this.data.set(d); this.loading.set(false); },
      error: err => {
        this.error.set(err?.error?.detail ?? 'Error al cargar el dashboard');
        this.loading.set(false);
      },
    });
  }

  aplicarFiltros() { this.cargar(); }

  limpiarFiltros() {
    this.fechaDesde = '';
    this.fechaHasta = '';
    this.clasificacion = '';
    this.cargar();
  }

  barWidth(val: number, max: number): string {
    return max > 0 ? `${Math.round((val / max) * 100)}%` : '0%';
  }

  formatFecha(iso: string): string {
    const d = new Date(iso);
    return `${d.getDate()}/${d.getMonth() + 1}`;
  }

  getSlaColor(sla: number): string {
    if (sla >= 80) return '#10b981';
    if (sla >= 50) return '#f59e0b';
    return '#ef4444';
  }

  getEstadoColor(estado: string): string {
    const map: Record<string, string> = {
      COMPLETADO:   '#10b981',
      CANCELADO:    '#ef4444',
      ASIGNADO:     '#3b82f6',
      EN_CAMINO:    '#8b5cf6',
      EN_ATENCION:  '#f59e0b',
      REPORTADO:    '#64748b',
    };
    return map[estado] ?? '#94a3b8';
  }

  clasifTotal = computed(() =>
    this.data()?.por_clasificacion.reduce((s, c) => s + c.total, 0) ?? 0
  );

  trackNombre(_: number, item: { nombre: string }) { return item.nombre; }
  trackFecha(_: number, item: { fecha: string }) { return item.fecha; }
}
