import { Component, signal, computed, ViewEncapsulation, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../core/services/auth.service';
import { BitacoraService } from '../../services/bitacora.service';

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
export class DashboardComponent implements OnInit {
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
      section: 'ADMINISTRACIÓN',
      expanded: true,
      items: [
        { label: 'Usuarios',        icon: 'users',  route: '/dashboard/usuarios', roles: ['ADMINISTRADOR'] },
        { label: 'Roles y Permisos',icon: 'shield', route: '/dashboard/roles',    roles: ['ADMINISTRADOR'] },
        { label: 'Bitácora',        icon: 'archive',route: '/dashboard/bitacora', roles: ['ADMINISTRADOR'] },
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
        { label: 'Vehículos', icon: 'truck',   route: '/dashboard/vehiculos', roles: ['ADMINISTRADOR', 'CLIENTE'] },
      ],
    },
    {
      section: 'GESTIÓN DE INCIDENTES',
      expanded: true,
      items: [
        { label: 'Registrar incidente', icon: 'plus-circle', route: '/dashboard/incidentes/nuevo', roles: ['ADMINISTRADOR', 'CLIENTE'] },
        { label: 'Incidentes', icon: 'alert-triangle', route: '/dashboard/incidentes', roles: ['ADMINISTRADOR', 'CLIENTE'] },
      ],
    },
    {
      section: 'ASIGNACIÃ“N Y ATENCIÃ“N',
      expanded: true,
      items: [
        { label: 'Solicitudes', icon: 'bell', route: '/dashboard/solicitudes-disponibles', roles: ['TALLER'] },
        { label: 'Mis Servicios', icon: 'list', route: '/dashboard/servicios', roles: ['ADMINISTRADOR', 'TALLER'] },
      ],
    },
    {
      section: 'MI CUENTA',
      expanded: true,
      items: [
        { label: 'Mi Perfil', icon: 'user', route: '/dashboard/perfil', roles: ['ADMINISTRADOR', 'TALLER', 'CLIENTE'] },
      ],
    },
  ]);

  visibleGroups = computed(() => {
    const rol = this.auth.rol;
    return this.navGroups()
      .map(g => ({ ...g, items: g.items.filter(i => i.roles.includes(rol)) }))
      .filter(g => g.items.length > 0);
  });

  constructor(public auth: AuthService, private router: Router, private bitacora: BitacoraService) {}

  ngOnInit() {
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe((e: any) => {
      if (typeof window !== 'undefined' && window.innerWidth < 768) {
        this.sidebarOpen.set(false);
      }
      
      // Auto-register navigation
      if (this.auth.getToken()) {
        let modulo = 'Navegación';
        let accion = 'Acceso a ' + e.urlAfterRedirects;
        
        // Simple map
        if (e.urlAfterRedirects.includes('/dashboard/usuarios')) modulo = 'Usuarios';
        else if (e.urlAfterRedirects.includes('/dashboard/roles')) modulo = 'Roles y Permisos';
        else if (e.urlAfterRedirects.includes('/dashboard/talleres')) modulo = 'Talleres';
        else if (e.urlAfterRedirects.includes('/dashboard/vehiculos')) modulo = 'Vehículos';
        else if (e.urlAfterRedirects.includes('/dashboard/incidentes')) modulo = 'Incidentes';
        else if (e.urlAfterRedirects.includes('/dashboard/bitacora')) modulo = 'Bitácora';
        
        this.bitacora.logAction(modulo, accion).subscribe();
      }
    });
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
    };
    return icons[name] ?? '';
  }
}
