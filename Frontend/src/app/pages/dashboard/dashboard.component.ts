import { Component, signal, computed, ViewEncapsulation, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../core/services/auth.service';

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

  constructor(public auth: AuthService, private router: Router) {}

  ngOnInit() {
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => {
      if (typeof window !== 'undefined' && window.innerWidth < 768) {
        this.sidebarOpen.set(false);
      }
    });
  }

  toggleGroup(group: NavGroup) {
    this.navGroups.update(groups => 
      groups.map(g => g.section === group.section ? { ...g, expanded: !g.expanded } : g)
    );
  }

  logout() { this.auth.logout(); }
  toggleSidebar() { this.sidebarOpen.update(v => !v); }

  getIcon(name: string): string {
    const icons: Record<string, string> = {
      home:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
      users:  `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      shield: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
      wrench: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      tool:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>`,
      user:   `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    };
    return icons[name] ?? '';
  }
}
