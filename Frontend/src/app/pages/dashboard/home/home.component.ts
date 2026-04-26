import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { UsuarioService } from '../../../core/services/usuario.service';
import { TallerService } from '../../../core/services/taller.service';
import { IncidenteService } from '../../../core/services/incidente.service';
import { ReportesService } from '../../../services/reportes.service';

interface StatCard {
  label: string;
  value: string | number;
  sub: string;
  color: string;
  icon: string;
}

const ACCESOS_ADMIN = [
  { label: 'Usuarios',         route: '/dashboard/usuarios',  icon: 'users',  desc: 'Gestionar cuentas y estados' },
  { label: 'Talleres',         route: '/dashboard/talleres',  icon: 'wrench', desc: 'Aprobar y administrar talleres' },
  { label: 'Incidentes',       route: '/dashboard/incidentes', icon: 'alert',  desc: 'Supervisar todos los incidentes' },
  { label: 'Reportes',         route: '/dashboard/reportes',  icon: 'report', desc: 'Métricas y reportes del sistema' },
];

const ACCESOS_TALLER = [
  { label: 'Solicitudes',      route: '/dashboard/solicitudes-disponibles', icon: 'inbox',  desc: 'Ver solicitudes sin asignar' },
  { label: 'Mis Servicios',    route: '/dashboard/servicios',               icon: 'wrench', desc: 'Gestionar servicios asignados' },
  { label: 'Chat',             route: '/dashboard/chats',                   icon: 'chat',   desc: 'Comunicación con clientes' },
  { label: 'Notificaciones',   route: '/dashboard/notificaciones',          icon: 'bell',   desc: 'Alertas y avisos' },
];

const ACCESOS_CLIENTE = [
  { label: 'Registrar Incidente', route: '/dashboard/incidentes/nuevo', icon: 'alert',  desc: 'Reportar una emergencia vehicular' },
  { label: 'Mis Incidentes',      route: '/dashboard/incidentes',       icon: 'car',    desc: 'Ver estado de mis solicitudes' },
  { label: 'Mis Pagos',           route: '/dashboard/pagos',            icon: 'dollar', desc: 'Historial de pagos realizados' },
  { label: 'Mis Vehículos',       route: '/dashboard/vehiculos',        icon: 'car',    desc: 'Administrar vehículos registrados' },
];

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent implements OnInit {
  stats    = signal<StatCard[]>([]);
  loading  = signal(true);
  accesos: typeof ACCESOS_ADMIN = [];

  hora  = new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
  fecha = new Date().toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long' });

  // Taller metrics
  tallerMetricas = signal<any>(null);
  // Client metrics
  clienteMetricas = signal<any>(null);

  constructor(
    public auth: AuthService,
    private usuarioSrv: UsuarioService,
    private tallerSrv: TallerService,
    private incidenteSrv: IncidenteService,
    private reportesSrv: ReportesService,
  ) {}

  ngOnInit() {
    const rol = this.auth.rol;
    if (rol === 'ADMINISTRADOR') {
      this.accesos = ACCESOS_ADMIN as any;
      this.cargarStatsAdmin();
    } else if (rol === 'TALLER') {
      this.accesos = ACCESOS_TALLER as any;
      this.cargarStatsTaller();
    } else if (rol === 'CLIENTE') {
      this.accesos = ACCESOS_CLIENTE as any;
      this.cargarStatsCliente();
    } else {
      this.loading.set(false);
    }
  }

  private cargarStatsAdmin() {
    this.reportesSrv.resumen().subscribe({
      next: (r) => {
        this.stats.set([
          { label: 'Incidentes totales',  value: r.total_incidentes,       sub: `${r.incidentes_reportados} reportados · ${r.incidentes_en_proceso} en proceso`, color: 'blue',   icon: 'alert'  },
          { label: 'Usuarios registrados',value: r.total_usuarios,          sub: `${r.total_clientes} clientes · ${r.total_talleres} talleres`,                    color: 'teal',   icon: 'users'  },
          { label: 'Pagos completados',   value: r.total_pagos_completados, sub: 'Ingresos: $ ' + Number(r.ingresos_totales).toFixed(2),                             color: 'green',  icon: 'dollar' },
          { label: 'Comisión plataforma', value: '$ ' + Number(r.comision_plataforma_total).toFixed(2), sub: '10% de los servicios pagados',                        color: 'yellow', icon: 'report' },
        ]);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private cargarStatsTaller() {
    this.tallerSrv.misMetricas().subscribe({
      next: (m) => {
        this.tallerMetricas.set(m);
        this.stats.set([
          { label: 'Servicios recibidos', value: m.solicitudes_recibidas, sub: `${m.en_proceso} en proceso · ${m.cancelados} cancelados`, color: 'blue',   icon: 'inbox'  },
          { label: 'Completados',         value: m.completados,           sub: `${m.pagos_completados} pagos confirmados`,                   color: 'green',  icon: 'check'  },
          { label: 'Ingresos del taller', value: '$ ' + m.ingresos_taller.toFixed(2), sub: 'Después del 10% de comisión',                    color: 'teal',   icon: 'dollar' },
          { label: 'Comisión plataforma', value: '$ ' + m.comisiones_pagadas.toFixed(2), sub: '10% retenido por la plataforma',               color: 'yellow', icon: 'report' },
        ]);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private cargarStatsCliente() {
    this.incidenteSrv.misMetricasCliente().subscribe({
      next: (m) => {
        this.clienteMetricas.set(m);
        this.stats.set([
          { label: 'Mis incidentes',         value: m.total_incidentes,   sub: `${m.en_proceso} en atención · ${m.reportados} reportados`,  color: 'blue',   icon: 'car'    },
          { label: 'Pendientes de pago',      value: m.pendientes_de_pago, sub: 'Servicios resueltos sin pagar',                             color: 'yellow', icon: 'dollar' },
          { label: 'Servicios pagados',       value: m.pagados,            sub: 'Total gastado: $ ' + m.total_gastado.toFixed(2),              color: 'green',  icon: 'check'  },
          { label: 'Cancelados',              value: m.cancelados,         sub: 'Incidentes cancelados',                                      color: 'teal',   icon: 'alert'  },
        ]);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  getIcon(name: string): string {
    const icons: Record<string, string> = {
      users:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      wrench: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      alert:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      report: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
      dollar: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
      inbox:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>`,
      check:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
      car:    `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2h-2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>`,
      chat:   `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      bell:   `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
    };
    return icons[name] ?? '';
  }
}
