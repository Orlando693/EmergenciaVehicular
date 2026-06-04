import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { AuthService } from '../../../../../core/services/auth.service';

@Component({
  selector: 'app-gestionar-atencion-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './gestionar-atencion-list.component.html',
  styleUrls: ['./gestionar-atencion-list.component.css']
})
export class GestionarAtencionListComponent implements OnInit {
  incidentes: IncidenteOut[] = [];
  loading = true;
  error = '';
  esTaller = false;
  esCliente = false;

  /** Estados relevantes para gestionar estimaciones */
  private readonly estadosActivos = new Set(['EN_PROCESO', 'ASIGNADO', 'RESUELTO']);

  constructor(
    private incidenteService: IncidenteService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esTaller  = rol === 'TALLER';
    this.esCliente = rol === 'CLIENTE';
    this.cargarIncidentes();
  }

  cargarIncidentes(): void {
    this.loading = true;
    this.error = '';
    this.incidenteService.consultarHistorial().subscribe({
      next: (data: IncidenteOut[]) => {
        this.incidentes = data.filter(i => this.estadosActivos.has(i.estado));
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los servicios. Intenta nuevamente.';
        this.loading = false;
      }
    });
  }

  badgeClase(estado: string): string {
    const mapa: Record<string, string> = {
      ASIGNADO:   'bg-amber-100 text-amber-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO:   'bg-emerald-100 text-emerald-700',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-600';
  }
}
