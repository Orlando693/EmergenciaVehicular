import { Component, signal, computed, ViewEncapsulation, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../core/services/auth.service';
import { BitacoraService } from '../../services/bitacora.service';
import { NotificacionesService } from '../../services/notificaciones.service';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  roles: string[];
}

interface NavGroup {
  section: string;
  items: NavItem[];
  expanded?: boolean;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class DashboardComponent implements OnInit, OnDestroy {
  sidebarOpen = signal(typeof window !== 'undefined' ? window.innerWidth >= 768 : true);

  navGroups = signal<NavGroup[]>([
    {
      section: 'GENERAL',
      expanded: true,
      items: [
        { label: 'Inicio', icon: 'home', route: '/dashboard', roles: ['ADMINISTRADOR', 'TALLER', 'CLIENTE'] },
      ],
    },
    {
      section: 'ADMINISTRACION',
      expanded: true,
      items: [
        { label: 'Usuarios',        icon: 'users',  route: '/dashboard/usuarios', roles: ['ADMINISTRADOR'] },
        { label: 'Roles y Permisos',icon: 'shield', route: '/dashboard/roles',    roles: ['ADMINISTRADOR'] },
      ],
    },
    {
      section: 'OPERACIONES',
      expanded: true,
      items: [
        { label: 'Talleres', icon: 'wrench', route: '/dashboard/talleres', roles: ['ADMINISTRADOR', 'TALLER'] },
        { label: 'Técnicos', icon: 'tool',   route: '/dashboard/tecnicos', roles: ['ADMINISTRADOR', 'TALLER'] },
      ],
    },
    {
      section: 'GESTIÓN DE VEHÍCULOS',
      expanded: true,
      items: [
        { label: 'Vehículos', icon: 'truck',   route: '/dashboard/vehiculos', roles: ['CLIENTE'] },
      ],
    },
    {
      section: 'GESTIÓN DE INCIDENTES',
      expanded: true,
      items: [
        { label: 'Registrar incidente', icon: 'plus-circle', route: '/dashboard/incidentes/nuevo', roles: ['CLIENTE'] },
        { label: 'Incidentes', icon: 'alert-triangle', route: '/dashboard/incidentes', roles: ['ADMINISTRADOR', 'CLIENTE'] },
      ],
    },
    {
      section: 'ASIGNACION Y ATENCION',
      expanded: true,
      items: [
        { label: 'Solicitudes',    icon: 'bell',         route: '/dashboard/solicitudes-disponibles', roles: ['TALLER'] },
        { label: 'Mis Servicios',  icon: 'list',         route: '/dashboard/servicios',               roles: ['ADMINISTRADOR', 'TALLER'] },
        { label: 'Comunicación',   icon: 'chat',         route: '/dashboard/chats',                   roles: ['ADMINISTRADOR', 'TALLER', 'CLIENTE'] },
        { label: 'Notificaciones', icon: 'notification', route: '/dashboard/notificaciones',          roles: ['ADMINISTRADOR', 'TALLER', 'CLIENTE'] },
      ],
    },
    {
      section: 'GESTION DE SERVICIOS',      expanded: true,
      items: [
        { label: 'Mis Incidentes', icon: 'alert-triangle', route: '/dashboard/incidentes', roles: ['CLIENTE'] },
        { label: 'Mis Pagos',      icon: 'dollar',         route: '/dashboard/pagos',      roles: ['CLIENTE'] },
        { label: 'Pagos (Admin)',  icon: 'dollar',         route: '/dashboard/pagos',      roles: ['ADMINISTRADOR'] },
      ],
    },
    {
      section: 'MI CUENTA',
      expanded: true,
      items: [
        { label: 'Mi Perfil', icon: 'user', route: '/dashboard/perfil', roles: ['ADMINISTRADOR', 'TALLER', 'CLIENTE'] },
      ],
    },
    {
      section: 'BITACORA Y REPORTES',
      expanded: true,
      items: [
        { label: 'Bitácora',  icon: 'archive', route: '/dashboard/bitacora', roles: ['ADMINISTRADOR'] },
        { label: 'Reportes',  icon: 'report',  route: '/dashboard/reportes', roles: ['ADMINISTRADOR'] },
      ],
    },
  ]);

  visibleGroups = computed(() => {
    const rol = this.auth.rol;
    return this.navGroups()
      .map(g => ({ ...g, items: g.items.filter(i => i.roles.includes(rol)) }))
      .filter(g => g.items.length > 0);
  });

  constructor(public auth: AuthService, private router: Router, private bitacora: BitacoraService, public notif: NotificacionesService) {}

  ngOnInit() {
    // Conectar WebSocket de notificaciones
    const token = this.auth.getToken();
    if (token) {
      this.notif.conectar(token);
      this.notif.contarNoLeidas().subscribe({ next: r => this.notif.noLeidas.set(r.count) });
    }

    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe((e: any) => {
      if (typeof window !== 'undefined' && window.innerWidth < 768) {
        this.sidebarOpen.set(false);
      }

      if (this.auth.getToken()) {
        let modulo = 'Navegacion';
        let accion = 'Acceso a ' + e.urlAfterRedirects;

        if (e.urlAfterRedirects.includes('/dashboard/usuarios'))       modulo = 'Usuarios';
        else if (e.urlAfterRedirects.includes('/dashboard/roles'))     modulo = 'Roles y Permisos';
        else if (e.urlAfterRedirects.includes('/dashboard/talleres'))  modulo = 'Talleres';
        else if (e.urlAfterRedirects.includes('/dashboard/vehiculos')) modulo = 'Vehiculos';
        else if (e.urlAfterRedirects.includes('/dashboard/incidentes'))modulo = 'Incidentes';
        else if (e.urlAfterRedirects.includes('/dashboard/bitacora'))  modulo = 'Bitacora';
        else if (e.urlAfterRedirects.includes('/dashboard/notificaciones')) modulo = 'Notificaciones';

        this.bitacora.logAction(modulo, accion).subscribe();
      }
    });
  }

  ngOnDestroy() {
    this.notif.desconectar();
  }

  toggleGroup(group: NavGroup) {
    this.navGroups.update(groups => 
      groups.map(g => g.section === group.section ? { ...g, expanded: !g.expanded } : g)
    );
  }

  logout() {
    this.bitacora.logAction('Autenticación', `Cierre de sesión: ${this.auth.nombreCompleto}`).subscribe({
      complete: () => this.auth.logout(),
      error: () => this.auth.logout(),
    });
  }
  toggleSidebar() { this.sidebarOpen.update(v => !v); }

  getIcon(name: string): string {
    const icons: Record<string, string> = {
      home:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
      users:  `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      shield: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
      wrench: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      tool:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>`,
      user:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
      truck:  `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`,
      'alert-triangle': `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      list: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`,
      'plus-circle': `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>`,
      bell: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
      archive: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>`,
      notification: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
      chat: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      dollar: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
      report: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
    };
    return icons[name] ?? '';
  }
}
