import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

interface KpiTiempo { label: string; minutos: number | null; descripcion: string; }
interface TallerKpi  { nombre: string; total_asignados: number; total_completados: number; avg_minutos_resolucion: number | null; tasa_cumplimiento: number; }
interface SlaDetalle  { nivel: string; porcentaje: number; completados: number; total: number; objetivo: number; }

interface KpisData {
  tiempos:            KpiTiempo[];
  sla:                SlaDetalle;
  tasa_asignacion:    number;
  tasa_abandono:      number;
  talleres:           TallerKpi[];
  total_incidentes:   number;
  total_asignados:    number;
  total_completados:  number;
  total_cancelados:   number;
}

@Component({
  selector: 'app-kpis-atencion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './kpis-atencion.component.html',
  styleUrls: ['./kpis-atencion.component.css'],
})
export class KpisAtencionComponent implements OnInit {
  private api = `${environment.apiUrl}/kpis-atencion`;

  data    = signal<KpisData | null>(null);
  loading = signal(true);
  error   = signal('');

  fechaDesde    = '';
  fechaHasta    = '';
  clasificacion = '';

  maxAvgTaller = computed(() => {
    const d = this.data();
    if (!d) return 1;
    const vals = d.talleres.map(t => t.avg_minutos_resolucion ?? 0);
    return Math.max(...vals, 1);
  });

  constructor(private http: HttpClient, public auth: AuthService) {}

  ngOnInit() { this.cargar(); }

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

    this.http.get<KpisData>(this.api, { headers: this.headers, params }).subscribe({
      next: d => { this.data.set(d); this.loading.set(false); },
      error: e => { this.error.set(e?.error?.detail ?? 'Error al cargar KPIs'); this.loading.set(false); },
    });
  }

  aplicar() { this.cargar(); }
  limpiar()  { this.fechaDesde = ''; this.fechaHasta = ''; this.clasificacion = ''; this.cargar(); }

  formatMin(min: number | null): string {
    if (min === null || min === undefined) return '—';
    if (min < 60) return `${min} min`;
    const h = Math.floor(min / 60);
    const m = Math.round(min % 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }

  nivelColor(nivel: string): string {
    return { EXCELENTE: '#10b981', BUENO: '#3b82f6', REGULAR: '#f59e0b', BAJO: '#ef4444' }[nivel] ?? '#94a3b8';
  }

  slaDash(pct: number): string { return `${Math.min(pct, 100)}, 100`; }

  tiempoColor(min: number | null): string {
    if (min === null) return '#94a3b8';
    if (min <= 15)   return '#10b981';
    if (min <= 60)   return '#f59e0b';
    return '#ef4444';
  }

  barW(val: number | null, max: number): string {
    return val !== null ? `${Math.round((val / max) * 100)}%` : '0%';
  }

  trackNombre(_: number, t: { nombre: string }) { return t.nombre; }
  trackLabel(_: number, t: KpiTiempo) { return t.label; }
}
