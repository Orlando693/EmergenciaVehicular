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
        path: 'talleres',
        loadComponent: () => import('./pages/dashboard/talleres/talleres.component').then(m => m.TalleresComponent),
      },
      {
        path: 'tecnicos',
        loadComponent: () => import('./pages/dashboard/tecnicos/tecnicos.component').then(m => m.TecnicosComponent),
      },
      {
        path: 'perfil',
        loadComponent: () => import('./pages/dashboard/perfil/perfil.component').then(m => m.PerfilComponent),
      },
    ],
  },

  { path: '**', redirectTo: 'login' },
];
