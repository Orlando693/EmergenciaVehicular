import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

interface ItemConteo  { nombre: string; total: number; pct: number; }
interface ZonaItem    { zona:   string; total: number; pct: number; }
interface TendenciaDia{ fecha:  string; total: number; }
interface CruceItem   { tipo: string; estados: Record<string, number>; }

interface AnalisisData {
  total:             number;
  por_estado:        ItemConteo[];
  por_tipo:          ItemConteo[];
  por_zona:          ZonaItem[];
  tendencia:         TendenciaDia[];
  cruce_tipo_estado: CruceItem[];
}

const ESTADO_COLOR: Record<string, string> = {
  REPORTADO:   '#94a3b8',
  ASIGNADO:    '#6366f1',
  EN_CAMINO:   '#f59e0b',
  EN_ATENCION: '#3b82f6',
  COMPLETADO:  '#10b981',
  CANCELADO:   '#ef4444',
};

@Component({
  selector: 'app-incidentes-analisis',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidentes-analisis.component.html',
  styleUrls: ['./incidentes-analisis.component.css'],
})
export class IncidentesAnalisisComponent implements OnInit {
  private api = `${environment.apiUrl}/incidentes-analisis`;

  data    = signal<AnalisisData | null>(null);
  loading = signal(true);
  error   = signal('');

  fechaDesde = '';
  fechaHasta = '';
  filtroTipo = '';
  filtroEstado = '';
  filtroZona = '';

  readonly estadoColor = ESTADO_COLOR;

  maxTipo = computed(() => {
    const d = this.data();
    return Math.max(...(d?.por_tipo.map(t => t.total) ?? [1]), 1);
  });

  maxZona = computed(() => {
    const d = this.data();
    return Math.max(...(d?.por_zona.map(z => z.total) ?? [1]), 1);
  });

  maxTendencia = computed(() => {
    const d = this.data();
    return Math.max(...(d?.tendencia.map(t => t.total) ?? [1]), 1);
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
    if (this.fechaDesde)    params = params.set('fecha_desde',  new Date(this.fechaDesde).toISOString());
    if (this.fechaHasta)    params = params.set('fecha_hasta',  new Date(this.fechaHasta).toISOString());
    if (this.filtroTipo)    params = params.set('tipo',         this.filtroTipo);
    if (this.filtroEstado)  params = params.set('estado',       this.filtroEstado);
    if (this.filtroZona)    params = params.set('zona',         this.filtroZona);

    this.http.get<AnalisisData>(this.api, { headers: this.headers, params }).subscribe({
      next: d => { this.data.set(d); this.loading.set(false); },
      error: e => { this.error.set(e?.error?.detail ?? 'Error al cargar el análisis'); this.loading.set(false); },
    });
  }

  aplicar() { this.cargar(); }
  limpiar()  { this.fechaDesde = ''; this.fechaHasta = ''; this.filtroTipo = ''; this.filtroEstado = ''; this.filtroZona = ''; this.cargar(); }

  colorEstado(e: string): string  { return ESTADO_COLOR[e] ?? '#94a3b8'; }
  barW(val: number, max: number): string { return `${Math.round((val / max) * 100)}%`; }

  estadosOrden = ['REPORTADO', 'ASIGNADO', 'EN_CAMINO', 'EN_ATENCION', 'COMPLETADO', 'CANCELADO'];
  estadoLabel  = (e: string) => e.replace('_', ' ');

  cruceTotalTipo(c: CruceItem): number {
    return Object.values(c.estados).reduce((a, b) => a + b, 0);
  }
  cruceW(val: number, total: number): string {
    return total > 0 ? `${Math.round((val / total) * 100)}%` : '0%';
  }
  cruceVal(c: CruceItem, e: string): number {
    return (c.estados as Record<string, number | undefined>)[e] ?? 0;
  }

  trackFecha(_: number, t: TendenciaDia) { return t.fecha; }
  trackNombre(_: number, t: { nombre: string }) { return t.nombre; }
  trackZona(_: number, z: ZonaItem) { return z.zona; }
  trackTipo(_: number, c: CruceItem) { return c.tipo; }
}
