import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';
import { platformAuthGuard, platformGuestGuard } from './core/guards/platform-auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
  },

  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/dashboard/general/home/home.component').then(m => m.HomeComponent),
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./pages/dashboard/administracion/usuarios/usuarios.component').then(m => m.UsuariosComponent),
      },
      {
        path: 'roles',
        loadComponent: () => import('./pages/dashboard/administracion/roles/roles.component').then(m => m.RolesComponent),
      },
      {
        path: 'bitacora',
        loadComponent: () => import('./pages/dashboard/bitacora-reportes/bitacora/bitacora.component').then(m => m.BitacoraComponent),
      },
      {
        path: 'talleres',
        loadComponent: () => import('./pages/dashboard/operaciones/talleres/talleres.component').then(m => m.TalleresComponent),
      },
      {
        path: 'tecnicos',
        loadComponent: () => import('./pages/dashboard/operaciones/tecnicos/tecnicos.component').then(m => m.TecnicosComponent),
      },
      {
        path: 'vehiculos',
        loadComponent: () => import('./pages/dashboard/gestion-vehiculos/vehiculos/vehiculos-list/vehiculos-list.component').then(m => m.VehiculosListComponent),
      },
      {
        path: 'vehiculos/nuevo',
        loadComponent: () => import('./pages/dashboard/gestion-vehiculos/vehiculos/vehiculos-form/vehiculos-form.component').then(m => m.VehiculosFormComponent),
      },
      {
        path: 'vehiculos/editar/:id',
        loadComponent: () => import('./pages/dashboard/gestion-vehiculos/vehiculos/vehiculos-form/vehiculos-form.component').then(m => m.VehiculosFormComponent),
      },
      {
        path: 'incidentes',
        loadComponent: () => import('./pages/dashboard/gestion-incidentes/incidentes/incidentes-list/incidentes-list.component').then(m => m.IncidentesListComponent),
      },
      {
        path: 'incidentes/nuevo',
        loadComponent: () => import('./pages/dashboard/gestion-incidentes/incidentes/incidentes-form/incidentes-form.component').then(m => m.IncidentesFormComponent),
      },
      {
        path: 'incidentes/detalle/:id',
        loadComponent: () => import('./pages/dashboard/gestion-incidentes/incidentes/incidentes-detail/incidentes-detail.component').then(m => m.IncidentesDetailComponent),
      },
      {
        path: 'solicitudes-disponibles',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/solicitudes/solicitudes-list/solicitudes-list.component').then(m => m.SolicitudesListComponent),
      },
      {
        path: 'solicitudes-disponibles/detalle/:id',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/solicitudes/solicitudes-detail/solicitudes-detail.component').then(m => m.SolicitudesDetailComponent),
      },
      {
        path: 'servicios',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/servicios/servicios-list/servicios-list.component').then(m => m.ServiciosListComponent),
      },
      {
        path: 'servicios/detalle/:id',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/servicios/servicios-detail/servicios-detail.component').then(m => m.ServiciosDetailComponent),
      },
      {
        path: 'perfil',
        loadComponent: () => import('./pages/dashboard/mi-cuenta/perfil/perfil.component').then(m => m.PerfilComponent),
      },
      {
        path: 'notificaciones',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/notificaciones/notificaciones.component').then(m => m.NotificacionesComponent),
      },
      {
        path: 'chats',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/chat/chats-list.component').then(m => m.ChatsListComponent),
      },
      {
        path: 'chat/:id',
        loadComponent: () => import('./pages/dashboard/asignacion-atencion/chat/chat.component').then(m => m.ChatComponent),
      },
      {
        path: 'pagos',
        loadComponent: () => import('./pages/dashboard/gestion-servicios/pagos/mis-pagos.component').then(m => m.MisPagosComponent),
      },
      {
        path: 'pagos/checkout/:id',
        loadComponent: () => import('./pages/dashboard/gestion-servicios/pagos/pago-checkout.component').then(m => m.PagoCheckoutComponent),
      },
      {
        path: 'reportes',
        loadComponent: () => import('./pages/dashboard/bitacora-reportes/reportes/reportes.component').then(m => m.ReportesComponent),
      },
      {
        path: 'atencion-tiempo-real',
        loadComponent: () => import('./pages/dashboard/gestion-operativa-atencion/atencion-tiempo-real/atencion-tiempo-real.component').then(m => m.AtencionTiempoRealComponent),
      },
      {
        path: 'atencion-tiempo-real/:id',
        loadComponent: () => import('./pages/dashboard/gestion-operativa-atencion/atencion-tiempo-real/atencion-tiempo-real.component').then(m => m.AtencionTiempoRealComponent),
      },
      {
        path: 'sincronizacion-offline',
        loadComponent: () => import('./pages/dashboard/gestion-operativa-atencion/sincronizacion-offline/sincronizacion-offline.component').then(m => m.SincronizacionOfflineComponent),
      },
      {
        path: 'cotizaciones',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/cotizaciones/cotizaciones-list/cotizaciones-list.component').then(m => m.CotizacionesListComponent),
      },
      {
        path: 'cotizaciones/detalle/:id',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/cotizaciones/cotizaciones-detail/cotizaciones-detail.component').then(m => m.CotizacionesDetailComponent),
      },
      {
        path: 'seleccionar-taller',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/seleccionar-taller/seleccionar-taller-list/seleccionar-taller-list.component').then(m => m.SeleccionarTallerListComponent),
      },
      {
        path: 'gestionar-atencion',
        loadComponent: () => import('./pages/dashboard/gestion-operativa-atencion/gestionar-atencion-reparacion/gestionar-atencion-list/gestionar-atencion-list.component').then(m => m.GestionarAtencionListComponent),
      },
      {
        path: 'gestionar-atencion/:id',
        loadComponent: () => import('./pages/dashboard/gestion-operativa-atencion/gestionar-atencion-reparacion/gestionar-atencion-form/gestionar-atencion-form.component').then(m => m.GestionarAtencionFormComponent),
      },
      {
        path: 'seleccionar-taller/:id',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/seleccionar-taller/seleccionar-taller-comparar/seleccionar-taller-comparar.component').then(m => m.SeleccionarTallerCompararComponent),
      },
      {
        path: 'procesar-pago',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/procesar-pago-pasarela/procesar-pago-list/procesar-pago-list.component').then(m => m.ProcesarPagoListComponent),
      },
      {
        path: 'procesar-pago/:id',
        loadComponent: () => import('./pages/dashboard/gestion-comercial-servicio/procesar-pago-pasarela/procesar-pago-checkout/procesar-pago-checkout.component').then(m => m.ProcesarPagoCheckoutComponent),
      },
      {
        path: 'planes',
        loadComponent: () => import('./pages/dashboard/planes/planes-list/planes-list.component').then(m => m.PlanesListComponent),
      },
      {
        path: 'backup',
        loadComponent: () => import('./pages/dashboard/bitacora-reportes/backup/backup.component').then(m => m.BackupComponent),
      },
      {
        path: 'dashboard-operacional',
        loadComponent: () => import('./pages/dashboard/gestion-control-analitica-saas/dashboard-operacional/dashboard-operacional.component').then(m => m.DashboardOperacionalComponent),
      },
      {
        path: 'kpis-atencion',
        loadComponent: () => import('./pages/dashboard/gestion-control-analitica-saas/kpis-atencion/kpis-atencion.component').then(m => m.KpisAtencionComponent),
      },
      {
        path: 'incidentes-analisis',
        loadComponent: () => import('./pages/dashboard/gestion-control-analitica-saas/incidentes-analisis/incidentes-analisis.component').then(m => m.IncidentesAnalisisComponent),
      },
      {
        path: 'multi-tenant-admin',
        loadComponent: () => import('./pages/dashboard/gestion-control-analitica-saas/multi-tenant-admin/multi-tenant-admin.component').then(m => m.MultiTenantAdminComponent),
      },
    ],
  },

  // ── SaaS SuperAdmin platform ──────────────────────────────────────────────
  {
    path: 'platform/login',
    canActivate: [platformGuestGuard],
    loadComponent: () =>
      import('./pages/plataform/login/platform-login.component').then(m => m.PlatformLoginComponent),
  },
  {
    path: 'platform/dashboard',
    canActivate: [platformAuthGuard],
    loadComponent: () =>
      import('./pages/plataform/dashboard/platform-dashboard.component').then(m => m.PlatformDashboardComponent),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/plataform/dashboard/organizaciones/organizaciones.component').then(m => m.OrganizacionesComponent),
      },
      {
        path: 'reportes',
        loadComponent: () =>
          import('./pages/plataform/dashboard/reportes-predictivos/reportes-predictivos.component').then(m => m.ReportesPredictivosComponent),
      },
    ],
  },

  { path: '**', redirectTo: 'login' },
];
