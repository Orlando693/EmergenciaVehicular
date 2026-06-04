import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { AuthService } from '../../../../../core/services/auth.service';

@Component({
  selector: 'app-procesar-pago-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './procesar-pago-list.component.html',
  styleUrls: ['./procesar-pago-list.component.css']
})
export class ProcesarPagoListComponent implements OnInit {
  incidentes: IncidenteOut[] = [];
  loading = true;
  error = '';

  /** Estados donde el pago puede ejecutarse */
  private readonly estadosPagables = new Set(['EN_PROCESO', 'RESUELTO', 'PAGADO']);

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
        this.incidentes = data.filter(i => this.estadosPagables.has(i.estado));
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los servicios. Intenta nuevamente.';
        this.loading = false;
      }
    });
  }

  get pendientePago(): IncidenteOut[] {
    return this.incidentes.filter(i => i.estado !== 'PAGADO');
  }

  get yaPagados(): IncidenteOut[] {
    return this.incidentes.filter(i => i.estado === 'PAGADO');
  }

  badgeClase(estado: string): string {
    const mapa: Record<string, string> = {
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO:   'bg-emerald-100 text-emerald-700',
      PAGADO:     'bg-violet-100 text-violet-700',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-600';
  }
}
