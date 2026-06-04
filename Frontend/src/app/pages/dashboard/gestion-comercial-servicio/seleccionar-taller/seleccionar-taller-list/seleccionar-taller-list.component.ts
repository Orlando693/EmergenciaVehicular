import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { AuthService } from '../../../../../core/services/auth.service';

@Component({
  selector: 'app-seleccionar-taller-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './seleccionar-taller-list.component.html',
  styleUrls: ['./seleccionar-taller-list.component.css']
})
export class SeleccionarTallerListComponent implements OnInit {
  incidentes: IncidenteOut[] = [];
  loading = true;
  error = '';

  /** Estados en que tiene sentido comparar talleres */
  private readonly estadosPendientes = new Set(['REPORTADO', 'EN_PROCESO']);

  constructor(
    private incidenteService: IncidenteService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.cargarIncidentes();
  }

  cargarIncidentes(): void {
    this.loading = true;
    this.error = '';
    this.incidenteService.consultarHistorial().subscribe({
      next: (data: IncidenteOut[]) => {
        this.incidentes = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar las emergencias. Intenta nuevamente.';
        this.loading = false;
      }
    });
  }

  /** Emergencias donde aún se puede comparar / seleccionar taller */
  get incidentesConCotizaciones(): IncidenteOut[] {
    return this.incidentes.filter(i =>
      this.estadosPendientes.has(i.estado) || !i.id_taller
    );
  }

  get incidentesConTaller(): IncidenteOut[] {
    return this.incidentes.filter(i => !!i.id_taller);
  }

  badgeClase(estado: string): string {
    const mapa: Record<string, string> = {
      REPORTADO:  'bg-amber-100 text-amber-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO:   'bg-emerald-100 text-emerald-700',
      PAGADO:     'bg-violet-100 text-violet-700',
      CANCELADO:  'bg-rose-100 text-rose-700',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-600';
  }
}
