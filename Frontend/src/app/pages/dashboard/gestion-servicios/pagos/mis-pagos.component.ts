import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { PagoService, PagoOut } from '../../../../services/pago.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-mis-pagos',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './mis-pagos.component.html',
})
export class MisPagosComponent implements OnInit {
  private pagoSvc = inject(PagoService);
  public  auth    = inject(AuthService);

  items   = signal<PagoOut[]>([]);
  total   = signal(0);
  loading = signal(true);

  readonly pageSize = 20;
  page       = signal(1);
  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    const skip = (this.page() - 1) * this.pageSize;
    const obs = this.auth.rol === 'ADMINISTRADOR'
      ? this.pagoSvc.todosPagos(skip, this.pageSize)
      : this.pagoSvc.misPagos(skip, this.pageSize);

    obs.subscribe({
      next: (res) => { this.items.set(res.items); this.total.set(res.total); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  goToPage(p: number) {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.cargar();
  }

  pages() { return Array.from({ length: this.totalPages() }, (_, i) => i + 1); }

  estadoClass(estado: string): string {
    const map: Record<string, string> = {
      COMPLETADO: 'bg-emerald-100 text-emerald-700',
      PENDIENTE:  'bg-yellow-100 text-yellow-700',
      FALLIDO:    'bg-red-100 text-red-700',
    };
    return map[estado] ?? 'bg-slate-100 text-slate-600';
  }

  metodoBadge(metodo: string): string {
    const map: Record<string, string> = {
      TARJETA_CREDITO: '💳 Crédito',
      TARJETA_DEBITO:  '💰 Débito',
      TRANSFERENCIA:   '🏦 Transferencia',
      EFECTIVO:        '💵 Efectivo',
    };
    return map[metodo] ?? metodo;
  }
}
