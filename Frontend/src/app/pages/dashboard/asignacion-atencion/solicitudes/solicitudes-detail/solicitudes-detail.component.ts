import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { TallerService } from '../../../../../core/services/taller.service';
import { IncidenteOut } from '../../../../../core/services/incidente.service';

@Component({
  selector: 'app-solicitudes-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './solicitudes-detail.component.html',
  styleUrl: './solicitudes-detail.component.css',
})
export class SolicitudesDetailComponent implements OnInit {
  private tallerService = inject(TallerService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  id        = signal<number | null>(null);
  solicitud = signal<IncidenteOut | null>(null);
  cargando  = signal<boolean>(false);
  error     = signal<string | null>(null);
  okMsg     = signal<string | null>(null);
  procesando = signal<boolean>(false);

  mostrarRechazo = signal<boolean>(false);
  motivoRechazo  = '';

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.id.set(Number(idParam));
      this.cargarSolicitud();
    }
  }

  cargarSolicitud() {
    this.cargando.set(true);
    this.error.set(null);
    this.tallerService.detalleSolicitudDisponible(this.id()!).subscribe({
      next: (data) => { this.solicitud.set(data); this.cargando.set(false); },
      error: () => {
        this.error.set('No se pudieron cargar los detalles de esta solicitud o ya no está disponible.');
        this.cargando.set(false);
      }
    });
  }

  aceptar() {
    if (!this.id()) return;
    this.procesando.set(true);
    this.error.set(null);
    this.okMsg.set(null);
    this.tallerService.aceptarSolicitud(this.id()!).subscribe({
      next: (inc) => {
        this.okMsg.set('Solicitud aceptada. El cliente fue notificado y la solicitud está ahora en tus servicios.');
        this.procesando.set(false);
        setTimeout(() => this.router.navigate(['/dashboard/servicios/detalle', inc.id_incidente]), 900);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo aceptar la solicitud.');
        this.procesando.set(false);
      }
    });
  }

  abrirRechazo()  { this.mostrarRechazo.set(true); }
  cancelarRechazo() { this.mostrarRechazo.set(false); this.motivoRechazo = ''; }

  confirmarRechazo() {
    if (!this.id()) return;
    this.procesando.set(true);
    this.error.set(null);
    this.okMsg.set(null);
    this.tallerService.rechazarSolicitud(this.id()!, this.motivoRechazo?.trim() || undefined).subscribe({
      next: () => {
        this.okMsg.set('Solicitud rechazada. Sigue disponible para otro taller.');
        this.procesando.set(false);
        this.mostrarRechazo.set(false);
        this.motivoRechazo = '';
        setTimeout(() => this.router.navigate(['/dashboard/solicitudes-disponibles']), 900);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo rechazar la solicitud.');
        this.procesando.set(false);
      }
    });
  }

  volver() { this.router.navigate(['/dashboard/solicitudes-disponibles']); }

  badgeClasificacion(clas?: string | null): string {
    const map: Record<string, string> = {
      COLISION:   'bg-red-100 text-red-700',
      MECANICO:   'bg-amber-100 text-amber-700',
      NEUMATICOS: 'bg-emerald-100 text-emerald-700',
      ELECTRICO:  'bg-violet-100 text-violet-700',
    };
    return map[(clas || '').toUpperCase()] ?? 'bg-slate-100 text-slate-600';
  }

  prioridadTexto(clas?: string | null): string {
    const c = (clas || '').toUpperCase();
    if (c === 'COLISION')  return 'Alta';
    if (c === 'ELECTRICO') return 'Alta';
    if (c === 'MECANICO')  return 'Media';
    if (c === 'NEUMATICOS')return 'Media';
    return 'Normal';
  }

  prioridadClasses(clas?: string | null): string {
    const t = this.prioridadTexto(clas);
    if (t === 'Alta')  return 'bg-red-100 text-red-700';
    if (t === 'Media') return 'bg-amber-100 text-amber-700';
    return 'bg-emerald-100 text-emerald-700';
  }
}
