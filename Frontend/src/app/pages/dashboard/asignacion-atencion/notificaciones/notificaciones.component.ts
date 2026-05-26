import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { NotificacionesService, Notificacion } from '../../../../services/notificaciones.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-notificaciones',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './notificaciones.component.html',
})
export class NotificacionesComponent implements OnInit {
  private svc = inject(NotificacionesService);
  private auth = inject(AuthService);
  private router = inject(Router);

  items       = signal<Notificacion[]>([]);
  total       = signal(0);
  noLeidas    = signal(0);
  loading     = signal(true);
  marcando    = signal(false);

  readonly pageSize = 20;
  page      = signal(1);
  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));
  pages      = computed(() => Array.from({ length: this.totalPages() }, (_, i) => i + 1));

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    const skip = (this.page() - 1) * this.pageSize;
    this.svc.listar(skip, this.pageSize).subscribe({
      next: (res) => {
        this.items.set(res.items);
        this.total.set(res.total);
        this.noLeidas.set(res.no_leidas);
        this.svc.noLeidas.set(res.no_leidas);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  goToPage(p: number) {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.cargar();
  }

  marcarLeida(notif: Notificacion) {
    if (notif.leida) return;
    this.svc.marcarLeida(notif.id_notificacion).subscribe({
      next: () => {
        this.items.update(list =>
          list.map(n => n.id_notificacion === notif.id_notificacion ? { ...n, leida: true } : n)
        );
        this.noLeidas.update(n => Math.max(0, n - 1));
        this.svc.noLeidas.update(n => Math.max(0, n - 1));
      },
    });
  }

  marcarTodas() {
    this.marcando.set(true);
    this.svc.marcarTodasLeidas().subscribe({
      next: () => {
        this.items.update(list => list.map(n => ({ ...n, leida: true })));
        this.noLeidas.set(0);
        this.svc.noLeidas.set(0);
        this.marcando.set(false);
      },
      error: () => this.marcando.set(false),
    });
  }

  iconoTipo(tipo: string): string {
    const map: Record<string, string> = {
      NUEVO_INCIDENTE: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      ASIGNACION:      `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
      ESTADO_CAMBIO:   `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>`,
      NUEVO_SERVICIO:  `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`,
    };
    return map[tipo] ?? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
  }

  colorTipo(tipo: string): string {
    const map: Record<string, string> = {
      NUEVO_INCIDENTE: 'bg-orange-100 text-orange-600',
      ASIGNACION:      'bg-blue-100 text-blue-600',
      ESTADO_CAMBIO:   'bg-emerald-100 text-emerald-600',
      NUEVO_SERVICIO:  'bg-violet-100 text-violet-600',
      MENSAJE_CHAT:    'bg-cyan-100 text-cyan-600',
      PAGO_REALIZADO:  'bg-amber-100 text-amber-700',
      PAGO_RECIBIDO:   'bg-amber-100 text-amber-700',
    };
    return map[tipo] ?? 'bg-slate-100 text-slate-500';
  }

  /**
   * A3 - Resuelve la mejor ruta según rol y tipo de notificación.
   * - TALLER + NUEVO_INCIDENTE → solicitudes-disponibles/detalle/:id
   * - TALLER + cualquier otra (asignación, estado, pago, chat) → servicios/detalle/:id
   * - CUALQUIER ROL + MENSAJE_CHAT → /dashboard/chat/:id
   * - CLIENTE / ADMIN → incidentes/detalle/:id
   */
  rutaNotificacion(n: Notificacion): any[] | null {
    if (!n.id_incidente) return null;
    const rol = (this.auth.rol || '').toUpperCase();
    const tipo = (n.tipo || '').toUpperCase();

    if (tipo === 'MENSAJE_CHAT') {
      return ['/dashboard/chat', n.id_incidente];
    }

    if (rol === 'TALLER') {
      if (tipo === 'NUEVO_INCIDENTE') {
        return ['/dashboard/solicitudes-disponibles/detalle', n.id_incidente];
      }
      return ['/dashboard/servicios/detalle', n.id_incidente];
    }

    return ['/dashboard/incidentes/detalle', n.id_incidente];
  }

  etiquetaEnlace(n: Notificacion): string {
    const rol = (this.auth.rol || '').toUpperCase();
    const tipo = (n.tipo || '').toUpperCase();

    if (tipo === 'MENSAJE_CHAT') return `Abrir chat del incidente #${n.id_incidente} →`;
    if (rol === 'TALLER' && tipo === 'NUEVO_INCIDENTE') return `Ver solicitud #${n.id_incidente} →`;
    if (rol === 'TALLER') return `Ver servicio #${n.id_incidente} →`;
    return `Ver incidente #${n.id_incidente} →`;
  }

  irNotificacion(n: Notificacion) {
    const ruta = this.rutaNotificacion(n);
    this.marcarLeida(n);
    if (ruta) this.router.navigate(ruta);
  }
}
