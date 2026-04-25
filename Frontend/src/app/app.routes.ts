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
        loadComponent: () => import('./pages/dashboard/home/home.component').then(m => m.HomeComponent),
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./pages/dashboard/usuarios/usuarios.component').then(m => m.UsuariosComponent),
      },
      {
        path: 'roles',
        loadComponent: () => import('./pages/dashboard/roles/roles.component').then(m => m.RolesComponent),
      },
      {
        path: 'bitacora',
        loadComponent: () => import('./pages/dashboard/bitacora/bitacora.component').then(m => m.BitacoraComponent),
      },
      {
        path: 'talleres',
        loadComponent: () => import('./pages/dashboard/talleres/talleres.component').then(m => m.TalleresComponent),
      },
      {
        path: 'tecnicos',
        loadComponent: () => import('./pages/dashboard/tecnicos/tecnicos.component').then(m => m.TecnicosComponent),
      },
      {
        path: 'vehiculos',
        loadComponent: () => import('./pages/dashboard/vehiculos/vehiculos-list/vehiculos-list.component').then(m => m.VehiculosListComponent),
      },
      {
        path: 'vehiculos/nuevo',
        loadComponent: () => import('./pages/dashboard/vehiculos/vehiculos-form/vehiculos-form.component').then(m => m.VehiculosFormComponent),
      },
      {
        path: 'vehiculos/editar/:id',
        loadComponent: () => import('./pages/dashboard/vehiculos/vehiculos-form/vehiculos-form.component').then(m => m.VehiculosFormComponent),
      },
      {
        path: 'incidentes',
        loadComponent: () => import('./pages/dashboard/incidentes/incidentes-list/incidentes-list.component').then(m => m.IncidentesListComponent),
      },
      {
        path: 'incidentes/nuevo',
        loadComponent: () => import('./pages/dashboard/incidentes/incidentes-form/incidentes-form.component').then(m => m.IncidentesFormComponent),
      },
      {
        path: 'incidentes/detalle/:id',
        loadComponent: () => import('./pages/dashboard/incidentes/incidentes-detail/incidentes-detail.component').then(m => m.IncidentesDetailComponent),
      },
      {
        path: 'solicitudes-disponibles',
        loadComponent: () => import('./pages/dashboard/incidentes/solicitudes-list/solicitudes-list.component').then(m => m.SolicitudesListComponent),
      },
      {
        path: 'solicitudes-disponibles/detalle/:id',
        loadComponent: () => import('./pages/dashboard/incidentes/solicitudes-detail/solicitudes-detail.component').then(m => m.SolicitudesDetailComponent),
      },
      {
        path: 'servicios',
        loadComponent: () => import('./pages/dashboard/servicios/servicios-list/servicios-list.component').then(m => m.ServiciosListComponent),
      },
      {
        path: 'servicios/detalle/:id',
        loadComponent: () => import('./pages/dashboard/servicios/servicios-detail/servicios-detail.component').then(m => m.ServiciosDetailComponent),
      },
      {
        path: 'perfil',
        loadComponent: () => import('./pages/dashboard/perfil/perfil.component').then(m => m.PerfilComponent),
      },
    ],
  },

  { path: '**', redirectTo: 'login' },
];
