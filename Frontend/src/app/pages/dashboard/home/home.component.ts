import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { UsuarioService } from '../../../core/services/usuario.service';
import { TallerService } from '../../../core/services/taller.service';

interface StatCard {
  label: string;
  value: string | number;
  sub: string;
  color: string;
  icon: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class HomeComponent implements OnInit {
  stats = signal<StatCard[]>([]);
  loading = signal(true);
  hora = new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
  fecha = new Date().toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long' });

  accesos = [
    { label: 'Usuarios',         route: '/dashboard/usuarios',  icon: 'users',  desc: 'Gestionar cuentas y estados' },
    { label: 'Roles y Permisos', route: '/dashboard/roles',     icon: 'shield', desc: 'Control de acceso al sistema' },
    { label: 'Talleres',         route: '/dashboard/talleres',  icon: 'wrench', desc: 'Aprobar y administrar talleres' },
    { label: 'Técnicos',         route: '/dashboard/tecnicos',  icon: 'tool',   desc: 'Personal técnico por taller' },
  ];

  constructor(
    public auth: AuthService,
    private usuarioSrv: UsuarioService,
    private tallerSrv: TallerService,
  ) {}

  ngOnInit() {
    if (this.auth.rol === 'ADMINISTRADOR') {
      this.cargarStats();
    } else {
      this.loading.set(false);
    }
  }

  private cargarStats() {
    let usuarios: any[] = [];
    let talleres: any[] = [];
    let done = 0;

    const check = () => {
      done++;
      if (done < 2) return;

      const activos    = usuarios.filter(u => u.estado === 'ACTIVO').length;
      const bloqueados = usuarios.filter(u => u.estado === 'BLOQUEADO').length;
      const aprobados  = talleres.filter(t => t.estado_registro === 'APROBADO').length;
      const pendientes = talleres.filter(t => t.estado_registro === 'PENDIENTE').length;
      const tecnicos   = talleres.reduce((acc: number, t: any) => acc, 0);

      this.stats.set([
        { label: 'Usuarios totales',     value: usuarios.length, sub: `${activos} activos · ${bloqueados} bloqueados`, color: 'blue',   icon: 'users' },
        { label: 'Talleres registrados', value: talleres.length, sub: `${aprobados} aprobados · ${pendientes} pendientes`, color: 'green',  icon: 'wrench' },
        { label: 'Talleres pendientes',  value: pendientes,      sub: 'Esperando aprobación',                           color: 'yellow', icon: 'clock' },
        { label: 'Sistema',              value: 'Activo',        sub: 'Backend + Base de datos operativos',             color: 'teal',   icon: 'check' },
      ]);
      this.loading.set(false);
    };

    this.usuarioSrv.listar().subscribe({ next: (u) => { usuarios = u; check(); }, error: () => check() });
    this.tallerSrv.listar().subscribe({ next: (t) => { talleres = t; check(); }, error: () => check() });
  }

  getIcon(name: string): string {
    const icons: Record<string,string> = {
      users:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
      wrench: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      shield: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
      tool:   `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>`,
      clock:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
      check:  `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    };
    return icons[name] ?? '';
  }
}
