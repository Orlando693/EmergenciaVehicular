import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../core/services/incidente.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-chats-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './chats-list.component.html',
})
export class ChatsListComponent implements OnInit {
  private incSvc = inject(IncidenteService);
  public  auth   = inject(AuthService);

  incidentes = signal<IncidenteOut[]>([]);
  loading    = signal(true);

  ngOnInit() {
    this.incSvc.consultarHistorial().subscribe({
      next: (items) => {
        // Solo los que tienen taller asignado (chat disponible)
        const activos = items.filter(i => i.id_taller != null);
        this.incidentes.set(activos);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  estadoClass(estado: string): string {
    const map: Record<string, string> = {
      REPORTADO:  'bg-yellow-100 text-yellow-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO:   'bg-emerald-100 text-emerald-700',
      CANCELADO:  'bg-red-100 text-red-700',
    };
    return map[estado] ?? 'bg-slate-100 text-slate-600';
  }
}
