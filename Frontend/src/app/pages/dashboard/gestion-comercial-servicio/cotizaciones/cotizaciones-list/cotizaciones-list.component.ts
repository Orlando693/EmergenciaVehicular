import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CotizacionService, CotizacionReparacionOut, CotizacionSolicitudCreate } from '../../../../../services/cotizacion.service';
import { AuthService } from '../../../../../core/services/auth.service';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';

@Component({
  selector: 'app-cotizaciones-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './cotizaciones-list.component.html',
  styleUrls: ['./cotizaciones-list.component.css']
})
export class CotizacionesListComponent implements OnInit {
  cotizaciones: CotizacionReparacionOut[] = [];
  loading = true;
  error = '';
  esCliente = false;
  esTaller = false;

  // Modal solicitar cotización
  mostrarModal = false;
  incidentesDisponibles: IncidenteOut[] = [];
  loadingIncidentes = false;
  idIncidenteSeleccionado: number | null = null;
  descripcionSolicitud = '';
  enviando = false;
  errorModal = '';

  /** Estados de incidente que ya tienen taller asignado */
  private readonly estadosConTaller = new Set(['ASIGNADO', 'EN_PROCESO', 'RESUELTO']);

  constructor(
    private cotizacionService: CotizacionService,
    private incidenteService: IncidenteService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esCliente = rol === 'CLIENTE';
    this.esTaller  = rol === 'TALLER';
    this.cargarCotizaciones();
  }

  cargarCotizaciones(): void {
    this.loading = true;
    this.error = '';
    this.cotizacionService.listarCotizaciones().subscribe({
      next: (data) => { this.cotizaciones = data; this.loading = false; },
      error: () => { this.error = 'Error al cargar las cotizaciones'; this.loading = false; }
    });
  }

  // ── Modal solicitar ──────────────────────────────────────────────────────

  abrirModal(): void {
    this.mostrarModal = true;
    this.errorModal = '';
    this.idIncidenteSeleccionado = null;
    this.descripcionSolicitud = '';
    this.incidentesDisponibles = [];
    this.loadingIncidentes = true;

    this.incidenteService.consultarHistorial().subscribe({
      next: (lista) => {
        // Solo incidentes con taller asignado y sin cotización ya existente
        const conCot = new Set(this.cotizaciones.map(c => c.id_incidente));
        this.incidentesDisponibles = lista.filter(
          i => this.estadosConTaller.has(i.estado) && i.id_taller && !conCot.has(i.id_incidente)
        );
        this.loadingIncidentes = false;
      },
      error: () => { this.loadingIncidentes = false; }
    });
  }

  cerrarModal(): void { this.mostrarModal = false; }

  solicitarCotizacion(): void {
    if (!this.idIncidenteSeleccionado || this.enviando) return;
    this.enviando = true;
    this.errorModal = '';

    const payload: CotizacionSolicitudCreate = {
      id_incidente: this.idIncidenteSeleccionado,
      descripcion_solicitud: this.descripcionSolicitud.trim() || undefined
    };

    this.cotizacionService.solicitarCotizacion(payload).subscribe({
      next: () => {
        this.enviando = false;
        this.mostrarModal = false;
        this.cargarCotizaciones();
      },
      error: (err) => {
        this.errorModal = err?.error?.detail ?? 'Error al solicitar la cotización';
        this.enviando = false;
      }
    });
  }

  badgeClase(estado: string): string {
    const mapa: Record<string, string> = {
      PENDIENTE:  'bg-amber-100 text-amber-600',
      RESPONDIDA: 'bg-emerald-100 text-emerald-600',
      ACEPTADA:   'bg-blue-100 text-blue-600',
      RECHAZADA:  'bg-rose-100 text-rose-600',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-500';
  }
}
