import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { TallerService } from '../../../../../core/services/taller.service';

type FiltroId = 'TODOS' | 'EN_PROCESO' | 'RESUELTO' | 'PAGADO' | 'CANCELADO';

@Component({
  selector: 'app-servicios-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './servicios-list.component.html',
  styleUrl: './servicios-list.component.css',
})
export class ServiciosListComponent implements OnInit {
  private router         = inject(Router);
  private incidenteService = inject(IncidenteService);
  private tallerService  = inject(TallerService);

  incidentes = signal<IncidenteOut[]>([]);
  metricas   = signal<any | null>(null);
  cargando   = signal<boolean>(false);
  error      = signal<string | null>(null);

  filtro     = signal<FiltroId>('TODOS');
  filtros: { id: FiltroId; label: string }[] = [
    { id: 'TODOS',      label: 'Todos' },
    { id: 'EN_PROCESO', label: 'En proceso' },
    { id: 'RESUELTO',   label: 'Resueltos' },
    { id: 'PAGADO',     label: 'Pagados' },
    { id: 'CANCELADO',  label: 'Cancelados' },
  ];

  incidentesFiltrados = computed(() => {
    const f = this.filtro();
    if (f === 'TODOS') return this.incidentes();
    return this.incidentes().filter(i => i.estado === f);
  });

  ngOnInit(): void {
    this.cargarHistorial();
    this.cargarMetricas();
  }

  cargarHistorial() {
    this.cargando.set(true);
    this.incidenteService.consultarHistorial().subscribe({
      next: (data) => { this.incidentes.set(data); this.cargando.set(false); },
      error: () => { this.error.set('Error al cargar la lista de servicios.'); this.cargando.set(false); }
    });
  }

  cargarMetricas() {
    this.tallerService.misMetricas().subscribe({
      next: (m) => this.metricas.set(m),
      error: () => {},
    });
  }

  verDetalle(id: number) {
    this.router.navigate(['/dashboard/servicios/detalle', id]);
  }

  setFiltro(f: FiltroId) { this.filtro.set(f); }

  badgeClasificacion(clas?: string | null): string {
    const map: Record<string, string> = {
      COLISION:   'bg-red-100 text-red-700',
      MECANICO:   'bg-amber-100 text-amber-700',
      NEUMATICOS: 'bg-emerald-100 text-emerald-700',
      ELECTRICO:  'bg-violet-100 text-violet-700',
    };
    return map[(clas || '').toUpperCase()] ?? 'bg-slate-100 text-slate-600';
  }

  estadoBadge(estado: string): string {
    const map: Record<string, string> = {
      REPORTADO:  'bg-yellow-100 text-yellow-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO:   'bg-emerald-100 text-emerald-700',
      PAGADO:     'bg-teal-100 text-teal-700',
      CANCELADO:  'bg-red-100 text-red-700',
    };
    return map[estado] ?? 'bg-slate-100 text-slate-600';
  }
}
