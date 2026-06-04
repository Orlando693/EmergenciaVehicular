import { Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import {
  GestionarAtencionReparacionService,
  EstimacionAtencionOut,
} from '../../../../../services/gestionar-atencion-reparacion.service';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { AuthService } from '../../../../../core/services/auth.service';

@Component({
  selector: 'app-gestionar-atencion-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './gestionar-atencion-form.component.html',
  styleUrls: ['./gestionar-atencion-form.component.css']
})
export class GestionarAtencionFormComponent implements OnInit {
  idIncidente = 0;

  incidente: IncidenteOut | null = null;
  estimacion: EstimacionAtencionOut | null = null;

  loadingIncidente = true;
  loadingEstimacion = true;
  guardando = false;

  errorIncidente = '';
  errorEstimacion = '';
  mensajeExito = '';
  mensajeError = '';

  esTaller  = false;
  esCliente = false;

  /** Modo del formulario */
  modoEdicion = false;

  // Campos del formulario
  tiempoLlegada    = '';
  tiempoReparacion = '';
  observacion      = '';

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private atencionService: GestionarAtencionReparacionService,
    private incidenteService: IncidenteService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esTaller  = rol === 'TALLER';
    this.esCliente = rol === 'CLIENTE';

    this.idIncidente = Number(this.route.snapshot.paramMap.get('id'));
    this.cargarIncidente();
    this.cargarEstimacion();
  }

  cargarIncidente(): void {
    this.loadingIncidente = true;
    this.incidenteService.obtenerDetalle(this.idIncidente).subscribe({
      next: (data) => {
        this.incidente = data;
        this.loadingIncidente = false;
      },
      error: () => {
        this.errorIncidente = 'No se pudo cargar la información del servicio.';
        this.loadingIncidente = false;
      }
    });
  }

  cargarEstimacion(): void {
    this.loadingEstimacion = true;
    this.atencionService.obtenerEstimacion(this.idIncidente).subscribe({
      next: (data) => {
        this.estimacion = data;
        this.precargarFormulario(data);
        this.loadingEstimacion = false;
      },
      error: (err) => {
        if (err?.status === 404) {
          this.estimacion = null; // No hay estimación aún
        } else {
          this.errorEstimacion = 'Error al cargar la estimación.';
        }
        this.loadingEstimacion = false;
      }
    });
  }

  private precargarFormulario(est: EstimacionAtencionOut): void {
    this.tiempoLlegada    = est.tiempo_llegada    ?? '';
    this.tiempoReparacion = est.tiempo_reparacion ?? '';
    this.observacion      = est.observacion       ?? '';
  }

  activarEdicion(): void {
    if (this.estimacion) {
      this.precargarFormulario(this.estimacion);
    } else {
      this.tiempoLlegada = '';
      this.tiempoReparacion = '';
      this.observacion = '';
    }
    this.modoEdicion  = true;
    this.mensajeExito = '';
    this.mensajeError = '';
  }

  cancelarEdicion(): void {
    this.modoEdicion  = false;
    this.mensajeError = '';
  }

  private camposValidos(): boolean {
    return !!(this.tiempoLlegada.trim() || this.tiempoReparacion.trim());
  }

  guardar(): void {
    if (!this.camposValidos()) {
      this.mensajeError = 'Debes ingresar al menos el tiempo de llegada o el tiempo de reparación.';
      return;
    }
    this.guardando    = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    const payload = {
      tiempo_llegada:    this.tiempoLlegada.trim()    || null,
      tiempo_reparacion: this.tiempoReparacion.trim() || null,
      observacion:       this.observacion.trim()      || null,
    };

    const operacion$ = this.estimacion
      ? this.atencionService.actualizarEstimacion(this.idIncidente, payload)
      : this.atencionService.registrarEstimacion(this.idIncidente, payload);

    operacion$.subscribe({
      next: (data) => {
        this.estimacion  = data;
        this.modoEdicion = false;
        this.guardando   = false;
        this.mensajeExito = this.estimacion
          ? 'Estimación actualizada correctamente. El cliente ha sido notificado.'
          : 'Estimación registrada correctamente. El cliente ha sido notificado.';
      },
      error: (err) => {
        this.mensajeError = err?.error?.detail ?? 'Ocurrió un error al guardar. Intenta nuevamente.';
        this.guardando = false;
      }
    });
  }

  goBack(): void {
    this.location.back();
  }

  get loading(): boolean {
    return this.loadingIncidente || this.loadingEstimacion;
  }
}
