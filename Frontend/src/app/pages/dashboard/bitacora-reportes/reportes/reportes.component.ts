import { Component, signal, inject, OnDestroy, ViewEncapsulation } from '@angular/core';
import { CommonModule, DecimalPipe, TitleCasePipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ReportesService,
  ResumenGeneral, ReporteIncidentes, ReporteUsuarios,
  ReporteTalleres, ReportePagos,
} from '../../../../services/reportes.service';

type TabPrincipal = 'predefinidos' | 'ia';
type TipoReporte  = 'resumen' | 'incidentes' | 'usuarios' | 'talleres' | 'pagos';
type Formato      = 'csv' | 'pdf';

interface CartaPredefinida {
  key:     TipoReporte;
  titulo:  string;
  desc:    string;
  icon:    string;
  color:   string;
  bg:      string;
}

interface ResultadoIA {
  tipo:       TipoReporte;
  titulo:     string;
  resumen:    string;
  datos:      any;
  columnas:   string[];
  filas:      any[][];
  totales?:   string;
}

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe, TitleCasePipe, DatePipe],
  templateUrl: './reportes.component.html',
  styleUrls: ['./reportes.component.css'],
  encapsulation: ViewEncapsulation.None,
})
export class ReportesComponent implements OnDestroy {
  private svc = inject(ReportesService);

  /* ── tabs ──────────────────────────────────────────────── */
  tab = signal<TabPrincipal>('predefinidos');

  /* ── predefinidos ──────────────────────────────────────── */
  reporteActivo  = signal<TipoReporte | null>(null);
  loading        = signal(false);
  error          = signal('');

  resumen    = signal<ResumenGeneral  | null>(null);
  incidentes = signal<ReporteIncidentes | null>(null);
  usuarios   = signal<ReporteUsuarios | null>(null);
  talleres   = signal<ReporteTalleres | null>(null);
  pagos      = signal<ReportePagos    | null>(null);

  fInc  = { desde: '', hasta: '', estado: '', idTaller: '' };
  fUser = { desde: '', hasta: '', rol: '' };
  fPag  = { desde: '', hasta: '', estado: '', metodo: '' };

  readonly CARTAS: CartaPredefinida[] = [
    {
      key: 'resumen', titulo: 'Resumen General',
      desc: 'KPIs de incidentes, usuarios, talleres e ingresos de la plataforma.',
      icon: 'chart', color: 'text-violet-700', bg: 'bg-violet-50',
    },
    {
      key: 'incidentes', titulo: 'Reporte de Incidentes',
      desc: 'Lista de emergencias con estado, taller asignado y fechas. Filtrable.',
      icon: 'alert', color: 'text-amber-700', bg: 'bg-amber-50',
    },
    {
      key: 'usuarios', titulo: 'Reporte de Usuarios',
      desc: 'Listado de usuarios registrados, con roles, estado y fecha de alta.',
      icon: 'users', color: 'text-blue-700', bg: 'bg-blue-50',
    },
    {
      key: 'talleres', titulo: 'Reporte de Talleres',
      desc: 'Desempeño de cada taller: servicios atendidos, completados e ingresos.',
      icon: 'wrench', color: 'text-orange-700', bg: 'bg-orange-50',
    },
    {
      key: 'pagos', titulo: 'Reporte de Pagos',
      desc: 'Transacciones realizadas, métodos de pago, montos y comisiones.',
      icon: 'dollar', color: 'text-emerald-700', bg: 'bg-emerald-50',
    },
  ];

  /* ── IA / voz ──────────────────────────────────────────── */
  queryIA       = signal('');
  grabando      = signal(false);
  loadingIA     = signal(false);
  resultadoIA   = signal<ResultadoIA | null>(null);
  errorIA       = signal('');
  formatoSel    = signal<Formato>('csv');

  private recognition: any = null;

  /* ── lifecycle ─────────────────────────────────────────── */
  ngOnDestroy() { this.detenerGrabacion(); }

  /* ── Voz: Web Speech API ───────────────────────────────── */
  iniciarGrabacion() {
    const SR = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SR) {
      this.errorIA.set('Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge.');
      return;
    }
    this.recognition = new SR();
    this.recognition.lang           = 'es-ES';
    this.recognition.continuous     = false;
    this.recognition.interimResults = false;

    this.grabando.set(true);
    this.errorIA.set('');

    this.recognition.onresult = (e: any) => {
      const transcript: string = e.results[0][0].transcript;
      this.queryIA.set(transcript);
      this.grabando.set(false);
    };
    this.recognition.onerror = () => {
      this.errorIA.set('No se pudo capturar el audio. Verifica el micrófono.');
      this.grabando.set(false);
    };
    this.recognition.onend = () => this.grabando.set(false);
    this.recognition.start();
  }

  detenerGrabacion() {
    if (this.recognition) { this.recognition.stop(); this.recognition = null; }
    this.grabando.set(false);
  }

  toggleGrabacion() {
    this.grabando() ? this.detenerGrabacion() : this.iniciarGrabacion();
  }

  /* ── IA: interpretar y generar reporte ─────────────────── */
  async generarReporteIA() {
    const q = this.queryIA().trim();
    if (!q) { this.errorIA.set('Escribe o dicta tu consulta primero.'); return; }

    this.loadingIA.set(true);
    this.errorIA.set('');
    this.resultadoIA.set(null);

    const tipo   = this.detectarTipo(q);
    const fmt    = this.detectarFormato(q);
    if (fmt) this.formatoSel.set(fmt);

    try {
      const resultado = await this.ejecutarConsulta(tipo, q);
      this.resultadoIA.set(resultado);
    } catch {
      this.errorIA.set('Error al generar el reporte. Intenta de nuevo.');
    } finally {
      this.loadingIA.set(false);
    }
  }

  private detectarTipo(q: string): TipoReporte {
    const lq = q.toLowerCase();
    if (/incidente|emergencia|servicio|accidente/.test(lq)) return 'incidentes';
    if (/usuario|cliente|persona|registrado/.test(lq))      return 'usuarios';
    if (/taller|mecánico|mecanic|workshop/.test(lq))        return 'talleres';
    if (/pago|transacc|cobroingreso|factura|dinero/.test(lq)) return 'pagos';
    return 'resumen';
  }

  private detectarFormato(q: string): Formato | null {
    const lq = q.toLowerCase();
    if (/pdf|imprim/.test(lq))           return 'pdf';
    if (/excel|xls|xlsx|csv|hoja/.test(lq)) return 'csv';
    return null;
  }

  private ejecutarConsulta(tipo: TipoReporte, q: string): Promise<ResultadoIA> {
    return new Promise((resolve, reject) => {
      const obs$ = ((): any => {
        switch (tipo) {
          case 'resumen':    return this.svc.resumen();
          case 'incidentes': return this.svc.incidentes({});
          case 'usuarios':   return this.svc.usuarios({});
          case 'talleres':   return this.svc.talleres();
          default:           return this.svc.pagos({});
        }
      })();

      (obs$ as any).subscribe({
        next: (data: any) => resolve(this.transformarResultado(tipo, data, q)),
        error: reject,
      });
    });
  }

  private transformarResultado(tipo: TipoReporte, data: any, query: string): ResultadoIA {
    switch (tipo) {
      case 'resumen':
        return {
          tipo, titulo: 'Resumen General de la Plataforma',
          resumen: `Se encontraron ${data.total_incidentes} incidentes, ${data.total_usuarios} usuarios y $${data.ingresos_totales?.toFixed(2)} en ingresos.`,
          datos: data,
          columnas: ['Indicador', 'Valor'],
          filas: [
            ['Total incidentes',    data.total_incidentes],
            ['En proceso',          data.incidentes_en_proceso],
            ['Resueltos',           data.incidentes_resueltos],
            ['Total usuarios',      data.total_usuarios],
            ['Talleres aprobados',  data.total_talleres],
            ['Ingresos totales',    `$${(data.ingresos_totales ?? 0).toFixed(2)}`],
            ['Comisión plataforma', `$${(data.comision_plataforma_total ?? 0).toFixed(2)}`],
          ],
        };
      case 'incidentes':
        return {
          tipo, titulo: `Reporte de Incidentes (${data.total} registros)`,
          resumen: `Se encontraron ${data.total} incidentes. Distribución: ${Object.entries(data.por_estado).map(([k, v]) => `${k}: ${v}`).join(', ')}.`,
          datos: data,
          columnas: ['#', 'Clasificación IA', 'Estado', 'Taller', 'Dirección', 'Fecha'],
          filas: data.items.map((i: any) => [i.id_incidente, i.clasificacion_ia ?? '—', i.estado, i.taller_nombre ?? '—', i.direccion ?? '—', i.created_at?.slice(0, 10)]),
          totales: `Total: ${data.total}`,
        };
      case 'usuarios':
        return {
          tipo, titulo: `Reporte de Usuarios (${data.total} registros)`,
          resumen: `Se encontraron ${data.total} usuarios. Roles: ${Object.entries(data.por_rol).map(([k, v]) => `${k}: ${v}`).join(', ')}.`,
          datos: data,
          columnas: ['ID', 'Nombres', 'Apellidos', 'Email', 'Rol', 'Estado', 'Registro'],
          filas: data.items.map((u: any) => [u.id_usuario, u.nombres, u.apellidos, u.email, u.rol, u.estado, u.created_at?.slice(0, 10)]),
          totales: `Total: ${data.total}`,
        };
      case 'talleres':
        return {
          tipo, titulo: `Reporte de Talleres (${data.total} registros)`,
          resumen: `${data.total} talleres registrados con $${(data.total_ingresos ?? 0).toFixed(2)} en ingresos totales.`,
          datos: data,
          columnas: ['ID', 'Razón Social', 'Estado', 'Servicios', 'Completados', 'Ingresos'],
          filas: data.items.map((t: any) => [t.id_taller, t.razon_social, t.estado_registro, t.total_servicios, t.servicios_completados, `$${(t.ingresos_taller ?? 0).toFixed(2)}`]),
          totales: `Ingresos totales: $${(data.total_ingresos ?? 0).toFixed(2)}`,
        };
      default: // pagos
        return {
          tipo, titulo: `Reporte de Pagos (${data.total} transacciones)`,
          resumen: `${data.total} transacciones por un total de $${(data.monto_total ?? 0).toFixed(2)}. Comisión: $${(data.comision_total ?? 0).toFixed(2)}.`,
          datos: data,
          columnas: ['ID', 'Incidente', 'Método', 'Monto', 'Comisión', 'Estado', 'Fecha'],
          filas: data.items.map((p: any) => [p.id_pago, `#${p.id_incidente}`, p.metodo_pago, `$${(p.monto_total ?? 0).toFixed(2)}`, `$${(p.comision_plataforma ?? 0).toFixed(2)}`, p.estado, p.created_at?.slice(0, 10)]),
          totales: `Total: $${(data.monto_total ?? 0).toFixed(2)} | Comisión: $${(data.comision_total ?? 0).toFixed(2)}`,
        };
    }
  }

  /* ── Descarga CSV ──────────────────────────────────────── */
  descargarCSV(res: ResultadoIA) {
    const header = res.columnas.join(',');
    const rows   = res.filas.map(f => f.map(c => `"${c}"`).join(',')).join('\n');
    const csv    = '\ufeff' + header + '\n' + rows;
    const blob   = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    this.triggerDownload(blob, `reporte_${res.tipo}_${hoy()}.csv`);
  }

  /* ── Descarga PDF (ventana de impresión) ───────────────── */
  descargarPDF(res: ResultadoIA) {
    const html = `
      <!DOCTYPE html><html><head><meta charset="utf-8">
      <title>${res.titulo}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 32px; color: #1e293b; }
        h1   { font-size: 20px; margin-bottom: 4px; }
        p    { font-size: 13px; color: #64748b; margin-bottom: 16px; }
        table{ width: 100%; border-collapse: collapse; font-size: 12px; }
        th   { background: #f1f5f9; text-align: left; padding: 8px 10px; font-weight: 700; border-bottom: 2px solid #e2e8f0; }
        td   { padding: 7px 10px; border-bottom: 1px solid #e2e8f0; }
        tr:nth-child(even) td { background: #f8fafc; }
        .tot { font-weight: 700; background: #f1f5f9; padding: 8px 10px; text-align: right; }
        .foot{ font-size: 11px; color: #94a3b8; margin-top: 24px; }
      </style></head><body>
      <h1>${res.titulo}</h1>
      <p>${res.resumen}</p>
      <table>
        <thead><tr>${res.columnas.map(c => `<th>${c}</th>`).join('')}</tr></thead>
        <tbody>${res.filas.map(f => `<tr>${f.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>
      </table>
      ${res.totales ? `<div class="tot">${res.totales}</div>` : ''}
      <p class="foot">Generado: ${new Date().toLocaleString('es-ES')} · EmergenciaVehicular</p>
      </body></html>`;

    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 400);
  }

  private triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  /* ── Predefinidos: ejecutar reporte ────────────────────── */
  ejecutarPredefinido(key: TipoReporte) {
    this.reporteActivo.set(key);
    this.error.set('');
    if (key === 'resumen')    return this.cargarResumen();
    if (key === 'talleres')   return this.cargarTalleres();
  }

  cargarResumen() {
    this.loading.set(true);
    this.svc.resumen().subscribe({
      next: r  => { this.resumen.set(r);  this.loading.set(false); },
      error: () => { this.error.set('Error al cargar el resumen.'); this.loading.set(false); },
    });
  }

  cargarIncidentes() {
    this.loading.set(true);
    const f = { ...this.fInc, idTaller: this.fInc.idTaller ? Number(this.fInc.idTaller) : undefined };
    this.svc.incidentes(f as any).subscribe({
      next: r  => { this.incidentes.set(r);  this.loading.set(false); },
      error: () => { this.error.set('Error al cargar incidentes.'); this.loading.set(false); },
    });
  }

  cargarUsuarios() {
    this.loading.set(true);
    this.svc.usuarios(this.fUser).subscribe({
      next: r  => { this.usuarios.set(r);  this.loading.set(false); },
      error: () => { this.error.set('Error al cargar usuarios.'); this.loading.set(false); },
    });
  }

  cargarTalleres() {
    this.loading.set(true);
    this.svc.talleres().subscribe({
      next: r  => { this.talleres.set(r);  this.loading.set(false); },
      error: () => { this.error.set('Error al cargar talleres.'); this.loading.set(false); },
    });
  }

  cargarPagos() {
    this.loading.set(true);
    this.svc.pagos(this.fPag).subscribe({
      next: r  => { this.pagos.set(r);   this.loading.set(false); },
      error: () => { this.error.set('Error al cargar pagos.'); this.loading.set(false); },
    });
  }

  exportarCSVPredefinido(tipo: TipoReporte) {
    let csv = '';
    const fn = `reporte_${tipo}_${hoy()}.csv`;

    if (tipo === 'incidentes' && this.incidentes()) {
      csv = 'ID,Clasificacion,Estado,Taller,Direccion,Fecha\n';
      csv += this.incidentes()!.items.map(i =>
        `${i.id_incidente},"${i.clasificacion_ia ?? ''}",${i.estado},"${i.taller_nombre ?? ''}","${i.direccion ?? ''}",${i.created_at?.slice(0, 10)}`
      ).join('\n');
    } else if (tipo === 'usuarios' && this.usuarios()) {
      csv = 'ID,Nombres,Apellidos,Email,Rol,Estado,Fecha\n';
      csv += this.usuarios()!.items.map(u =>
        `${u.id_usuario},"${u.nombres}","${u.apellidos}","${u.email}",${u.rol},${u.estado},${u.created_at?.slice(0, 10)}`
      ).join('\n');
    } else if (tipo === 'talleres' && this.talleres()) {
      csv = 'ID,Razon Social,Estado,Servicios,Completados,Ingresos\n';
      csv += this.talleres()!.items.map(t =>
        `${t.id_taller},"${t.razon_social}",${t.estado_registro},${t.total_servicios},${t.servicios_completados},${t.ingresos_taller}`
      ).join('\n');
    } else if (tipo === 'pagos' && this.pagos()) {
      csv = 'ID,Incidente,Metodo,Monto,Comision,Estado,Fecha\n';
      csv += this.pagos()!.items.map(p =>
        `${p.id_pago},${p.id_incidente},${p.metodo_pago},${p.monto_total},${p.comision_plataforma},${p.estado},${p.created_at?.slice(0, 10)}`
      ).join('\n');
    } else { return; }

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    this.triggerDownload(blob, fn);
  }

  /* ── helpers ───────────────────────────────────────────── */
  estadoClass(e: string): string {
    const m: Record<string, string> = {
      REPORTADO: 'bg-yellow-100 text-yellow-700', EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO: 'bg-emerald-100 text-emerald-700', PAGADO: 'bg-green-100 text-green-700',
      CANCELADO: 'bg-red-100 text-red-700', ACTIVO: 'bg-emerald-100 text-emerald-700',
      COMPLETADO: 'bg-emerald-100 text-emerald-700', FALLIDO: 'bg-red-100 text-red-700',
      PENDIENTE: 'bg-yellow-100 text-yellow-700', APROBADO: 'bg-emerald-100 text-emerald-700',
    };
    return m[e] ?? 'bg-slate-100 text-slate-600';
  }

  objEntries = (obj: Record<string, any>) => obj ? Object.entries(obj) : [];

  getIcon(name: string): string {
    const icons: Record<string, string> = {
      chart: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>`,
      alert: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      users: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      wrench:`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      dollar:`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
      mic:   `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
      mic_off:`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
      download:`<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
      pdf:   `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
      stars: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/></svg>`,
      back:  `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>`,
    };
    return icons[name] ?? '';
  }
}

function hoy(): string {
  return new Date().toISOString().slice(0, 10);
}
