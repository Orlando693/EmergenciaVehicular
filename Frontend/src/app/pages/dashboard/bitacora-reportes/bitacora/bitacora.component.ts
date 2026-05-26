import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BitacoraService, LogEntry } from '../../../../services/bitacora.service';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bitacora.component.html',
})
export class BitacoraComponent implements OnInit {
  private bitacoraService = inject(BitacoraService);

  logs        = signal<LogEntry[]>([]);
  total       = signal(0);
  loading     = signal(true);
  deleting    = signal(false);
  confirmando = signal(false);

  readonly pageSize = 20;
  page = signal(1);

  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));
  pages      = computed(() => Array.from({ length: this.totalPages() }, (_, i) => i + 1));

  ngOnInit() { this.fetchLogs(); }

  fetchLogs() {
    this.loading.set(true);
    const skip = (this.page() - 1) * this.pageSize;
    this.bitacoraService.getLogs(skip, this.pageSize).subscribe({
      next: (res) => {
        this.logs.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  goToPage(p: number) {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.fetchLogs();
  }

  confirmarEliminar() { this.confirmando.set(true); }
  cancelarEliminar()  { this.confirmando.set(false); }

  eliminarTodo() {
    this.deleting.set(true);
    this.confirmando.set(false);
    this.bitacoraService.deleteAll().subscribe({
      next: () => {
        this.page.set(1);
        this.fetchLogs();
        this.deleting.set(false);
      },
      error: () => this.deleting.set(false),
    });
  }
}
