import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ReportesService,
  ResumenGeneral, ReporteIncidentes, ReporteUsuarios,
  ReporteTalleres, ReportePagos,
} from '../../../../services/reportes.service';

type Tab = 'resumen' | 'incidentes' | 'usuarios' | 'talleres' | 'pagos';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes.component.html',
})
export class ReportesComponent implements OnInit {
  private svc = inject(ReportesService);

  tab = signal<Tab>('resumen');
  loading = signal(false);
  error = signal<string | null>(null);

  resumen = signal<ResumenGeneral | null>(null);
  incidentes = signal<ReporteIncidentes | null>(null);
  usuarios = signal<ReporteUsuarios | null>(null);
  talleres = signal<ReporteTalleres | null>(null);
  pagos = signal<ReportePagos | null>(null);

  fInc = { desde: '', hasta: '', estado: '', idTaller: '' };
  fUser = { desde: '', hasta: '', rol: '' };
  fPagos = { desde: '', hasta: '', estado: '', metodo: '' };

  readonly TABS: { key: Tab; label: string; icon: string }[] = [
    { key: 'resumen', label: 'Resumen general', icon: 'report' },
    { key: 'incidentes', label: 'Incidentes', icon: 'alert' },
    { key: 'usuarios', label: 'Usuarios', icon: 'users' },
    { key: 'talleres', label: 'Talleres', icon: 'wrench' },
    { key: 'pagos', label: 'Pagos', icon: 'dollar' },
  ];

  ngOnInit() { this.cargarResumen(); }

  setTab(t: Tab) {
    this.tab.set(t);
    this.error.set(null);
    if (t === 'resumen' && !this.resumen()) this.cargarResumen();
    if (t === 'talleres' && !this.talleres()) this.cargarTalleres();
  }

  cargarResumen() {
    this.loading.set(true);
    this.svc.resumen().subscribe({
      next: r => { this.resumen.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar el resumen.'); this.loading.set(false); },
    });
  }

  cargarIncidentes() {
    this.loading.set(true);
    const f = { ...this.fInc, idTaller: this.fInc.idTaller ? Number(this.fInc.idTaller) : undefined };
    this.svc.incidentes(f as any).subscribe({
      next: r => { this.incidentes.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar incidentes.'); this.loading.set(false); },
    });
  }

  cargarUsuarios() {
    this.loading.set(true);
    this.svc.usuarios(this.fUser).subscribe({
      next: r => { this.usuarios.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar usuarios.'); this.loading.set(false); },
    });
  }

  cargarTalleres() {
    this.loading.set(true);
    this.svc.talleres().subscribe({
      next: r => { this.talleres.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar talleres.'); this.loading.set(false); },
    });
  }

  cargarPagos() {
    this.loading.set(true);
    this.svc.pagos(this.fPagos).subscribe({
      next: r => { this.pagos.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar pagos.'); this.loading.set(false); },
    });
  }

  estadoClass(e: string): string {
    const m: Record<string, string> = {
      REPORTADO: 'bg-yellow-100 text-yellow-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO: 'bg-emerald-100 text-emerald-700',
      PAGADO: 'bg-green-100 text-green-700',
      CANCELADO: 'bg-red-100 text-red-700',
      ACTIVO: 'bg-emerald-100 text-emerald-700',
      COMPLETADO: 'bg-emerald-100 text-emerald-700',
      FALLIDO: 'bg-red-100 text-red-700',
      PENDIENTE: 'bg-yellow-100 text-yellow-700',
      APROBADO: 'bg-emerald-100 text-emerald-700',
    };
    return m[e] ?? 'bg-slate-100 text-slate-600';
  }

  objEntries(obj: Record<string, any>): [string, any][] {
    return obj ? Object.entries(obj) : [];
  }

  getTabIcon(name: string): string {
    const icons: Record<string, string> = {
      report: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
      alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      users: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      wrench: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      dollar: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
    };
    return icons[name] ?? '';
  }

  exportarCSV(tipo: Tab) {
    let csv = '';
    const filename = `reporte_${tipo}_${new Date().toISOString().slice(0,10)}.csv`;

    if (tipo === 'incidentes' && this.incidentes()) {
      csv = 'ID,Clasificacion,Estado,Taller,Direccion,Fecha\n';
      csv += this.incidentes()!.items.map(i =>
        `${i.id_incidente},"${i.clasificacion_ia??''}",${i.estado},"${i.taller_nombre??''}","${i.direccion??''}",${i.created_at?.slice(0,10)}`
      ).join('\n');
    } else if (tipo === 'usuarios' && this.usuarios()) {
      csv = 'ID,Nombres,Apellidos,Email,Rol,Estado,Fecha Registro\n';
      csv += this.usuarios()!.items.map(u =>
        `${u.id_usuario},"${u.nombres}","${u.apellidos}","${u.email}",${u.rol},${u.estado},${u.created_at?.slice(0,10)}`
      ).join('\n');
    } else if (tipo === 'talleres' && this.talleres()) {
      csv = 'ID,Razon Social,Estado,Total Servicios,Completados,Ingresos\n';
      csv += this.talleres()!.items.map(t =>
        `${t.id_taller},"${t.razon_social}",${t.estado_registro},${t.total_servicios},${t.servicios_completados},${t.ingresos_taller}`
      ).join('\n');
    } else if (tipo === 'pagos' && this.pagos()) {
      csv = 'ID Pago,ID Incidente,Metodo,Monto Total,Monto Taller,Comision,Estado,Referencia,Fecha\n';
      csv += this.pagos()!.items.map(p =>
        `${p.id_pago},${p.id_incidente},${p.metodo_pago},${p.monto_total},${p.monto_taller},${p.comision_plataforma},${p.estado},"${p.referencia??''}",${p.created_at?.slice(0,10)}`
      ).join('\n');
    } else {
      return;
    }

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  imprimir() { window.print(); }
}
