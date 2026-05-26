import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

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
    ],
  },

  { path: '**', redirectTo: 'login' },
];
