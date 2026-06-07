import { Component, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { PlatformAuthService } from '../../../core/services/platform-auth.service';

interface PlatformNavItem {
  label: string;
  icon:  string;
  route: string;
}
interface PlatformNavGroup {
  section:  string;
  items:    PlatformNavItem[];
  expanded: boolean;
}

@Component({
  selector: 'app-platform-dashboard',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './platform-dashboard.component.html',
  styleUrls: ['./platform-dashboard.component.css'],
})
export class PlatformDashboardComponent {
  sidebarOpen = signal(typeof window !== 'undefined' ? window.innerWidth >= 768 : true);

  navGroups = signal<PlatformNavGroup[]>([
    {
      section: 'OPERACIÓN',
      expanded: true,
      items: [
        { label: 'Organizaciones', icon: 'org', route: '/platform/dashboard' },
      ],
    },
    {
      section: 'INTELIGENCIA',
      expanded: true,
      items: [
        { label: 'Reportes Predictivos', icon: 'chart', route: '/platform/dashboard/reportes' },
      ],
    },
  ]);

  constructor(public auth: PlatformAuthService) {}

  toggleSidebar() { this.sidebarOpen.update(v => !v); }

  toggleGroup(g: PlatformNavGroup) { g.expanded = !g.expanded; }

  logout() { this.auth.logout(); }

  getIcon(icon: string): string {
    const icons: Record<string, string> = {
      org: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2"/>
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
            </svg>`,
      chart: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>`,
    };
    return icons[icon] ?? icons['org'];
  }
}
