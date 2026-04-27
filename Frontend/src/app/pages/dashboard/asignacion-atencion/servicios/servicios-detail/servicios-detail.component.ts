import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { IncidenteService, IncidenteOut } from '../../../../../core/services/incidente.service';
import { AuthService } from '../../../../../core/services/auth.service';
import { PagoService, PagoOut, InfoPago } from '../../../../../services/pago.service';

@Component({
  selector: 'app-servicios-detail',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './servicios-detail.component.html',
  styleUrl: './servicios-detail.component.css',
})
export class ServiciosDetailComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private incidenteService = inject(IncidenteService);
  private pagoService = inject(PagoService);
  auth = inject(AuthService);

  id = signal<number | null>(null);
  solicitud = signal<IncidenteOut | null>(null);
  historialEstados = signal<any[]>([]);
  pagoInfo = signal<PagoOut | null>(null);
  costoInfo = signal<InfoPago | null>(null);

  cargando = signal<boolean>(false);
  cargandoHistorial = signal<boolean>(false);
  actualizando = signal<boolean>(false);

  error = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  estadoForm: FormGroup;

  constructor() {
    this.estadoForm = this.fb.group({
      estado: ['', Validators.required],
      observacion: [''],
    });
  }

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.id.set(Number(idParam));
      this.cargarServicio();
      this.cargarHistorial();
      this.cargarPago();
    }
  }

  cargarServicio() {
    this.cargando.set(true);
    this.incidenteService.obtenerDetalle(this.id()!).subscribe({
      next: (data) => {
        this.solicitud.set(data);
        this.estadoForm.patchValue({ estado: '' });
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo encontrar el detalle de este servicio.');
        this.cargando.set(false);
      },
    });
  }

  cargarHistorial() {
    this.cargandoHistorial.set(true);
    this.incidenteService.consultarHistorialEstados(this.id()!).subscribe({
      next: (data) => {
        this.historialEstados.set(data);
        this.cargandoHistorial.set(false);
      },
      error: () => this.cargandoHistorial.set(false),
    });
  }

  cargarPago() {
    // A2 - Usa /info que admite CLIENTE dueño, TALLER asignado o ADMIN.
    this.pagoService.infoPago(this.id()!).subscribe({
      next: (info) => {
        this.costoInfo.set(info);
        this.pagoInfo.set(info.pago_existente);
      },
      error: () => {
        this.costoInfo.set(null);
        this.pagoInfo.set(null);
      },
    });
  }

  actualizarEstado() {
    if (this.estadoForm.invalid) return;

    this.actualizando.set(true);
    this.error.set(null);
    this.successMsg.set(null);

    const payload = this.estadoForm.value;

    this.incidenteService.actualizarEstado(this.id()!, payload).subscribe({
      next: (updatedSol) => {
        this.successMsg.set('Estado actualizado. Se notificó al cliente.');
        this.solicitud.set(updatedSol);
        this.cargarHistorial();
        this.cargarPago();
        this.actualizando.set(false);
        this.estadoForm.patchValue({ estado: '', observacion: '' });
      },
      error: (err) => {
        this.error.set(err?.error?.detail || 'Error al actualizar el estado del servicio.');
        this.actualizando.set(false);
      },
    });
  }

  puedeActualizarEstado(sol: IncidenteOut): boolean {
    if (this.auth.rol !== 'TALLER') return false;
    return !['PAGADO', 'CANCELADO'].includes(sol.estado);
  }

  estadoBadge(estado: string): string {
    const map: Record<string, string> = {
      REPORTADO:  'bg-yellow-100 text-yellow-800',
      EN_PROCESO: 'bg-blue-100 text-blue-800',
      RESUELTO:   'bg-emerald-100 text-emerald-800',
      PAGADO:     'bg-teal-100 text-teal-800',
      CANCELADO:  'bg-rose-100 text-rose-800',
    };
    return map[estado] ?? 'bg-slate-100 text-slate-700';
  }

  prioridadTexto(clas?: string | null): string {
    const map: Record<string, string> = {
      COLISION:   'Alta',
      MECANICO:   'Media',
      ELECTRICO:  'Media',
      NEUMATICOS: 'Baja',
    };
    return map[(clas || '').toUpperCase()] ?? '—';
  }

  volver() {
    if (this.auth.rol === 'TALLER') {
      this.router.navigate(['/dashboard/servicios']);
    } else {
      this.router.navigate(['/dashboard/incidentes']);
    }
  }
}
