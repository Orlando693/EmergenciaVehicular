import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import {
  SeleccionarTallerService,
  CotizacionComparacionOut,
  SeleccionTallerOut,
} from '../../../../../services/seleccionar-taller.service';

@Component({
  selector: 'app-seleccionar-taller-comparar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './seleccionar-taller-comparar.component.html',
  styleUrls: ['./seleccionar-taller-comparar.component.css']
})
export class SeleccionarTallerCompararComponent implements OnInit {
  idIncidente = 0;

  cotizaciones: CotizacionComparacionOut[] = [];
  seleccionActual: SeleccionTallerOut | null = null;

  loading = true;
  error = '';

  /** Id de la cotización que el usuario resaltó para seleccionar */
  cotizacionDestacada: CotizacionComparacionOut | null = null;
  /** Muestra el cuadro de confirmación */
  mostrarConfirmacion = false;

  procesando = false;
  mensajeExito = '';
  mensajeError = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private seleccionarTallerService: SeleccionarTallerService
  ) {}

  ngOnInit(): void {
    this.idIncidente = Number(this.route.snapshot.paramMap.get('id'));
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading = true;
    this.error = '';

    // Verificar si ya hay selección activa
    this.seleccionarTallerService.obtenerSeleccionActual(this.idIncidente).subscribe({
      next: (sel) => {
        this.seleccionActual = sel;
        // Siempre cargar cotizaciones para mostrar el panel comparativo
        this.cargarCotizaciones();
      },
      error: () => {
        this.cargarCotizaciones();
      }
    });
  }

  cargarCotizaciones(): void {
    this.seleccionarTallerService.listarCotizaciones(this.idIncidente).subscribe({
      next: (data) => {
        this.cotizaciones = data;
        this.loading = false;
      },
      error: (err) => {
        const status = err?.status;
        if (status === 404) {
          this.error = 'No hay cotizaciones disponibles para esta emergencia. Espera a que los talleres respondan tu solicitud.';
        } else {
          this.error = 'No se pudieron cargar las cotizaciones. Intenta nuevamente.';
        }
        this.loading = false;
      }
    });
  }

  iniciarSeleccion(cotizacion: CotizacionComparacionOut): void {
    this.cotizacionDestacada = cotizacion;
    this.mostrarConfirmacion = true;
    this.mensajeError = '';
  }

  cancelarSeleccion(): void {
    this.mostrarConfirmacion = false;
    this.cotizacionDestacada = null;
  }

  confirmarSeleccion(): void {
    if (!this.cotizacionDestacada || this.procesando) return;

    this.procesando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    this.seleccionarTallerService.seleccionarTaller(this.idIncidente, {
      id_cotizacion: this.cotizacionDestacada.id_cotizacion
    }).subscribe({
      next: (resultado) => {
        this.seleccionActual = resultado;
        this.mensajeExito = resultado.mensaje;
        this.mostrarConfirmacion = false;
        this.cotizacionDestacada = null;
        this.procesando = false;
        // Recargar cotizaciones para reflejar estados actualizados
        this.cargarCotizaciones();
      },
      error: (err) => {
        const detail = err?.error?.detail ?? 'Ocurrió un error al seleccionar el taller. Intenta nuevamente.';
        this.mensajeError = detail;
        this.procesando = false;
      }
    });
  }

  esSeleccionada(cotizacion: CotizacionComparacionOut): boolean {
    return this.seleccionActual?.id_cotizacion_aceptada === cotizacion.id_cotizacion;
  }

  estrellas(calificacion: number | null): string[] {
    if (!calificacion) return Array(5).fill('empty');
    return Array.from({ length: 5 }, (_, i) => i < Math.round(calificacion) ? 'full' : 'empty');
  }

  badgeClase(estado: string): string {
    const mapa: Record<string, string> = {
      RESPONDIDA: 'bg-emerald-100 text-emerald-700',
      ACEPTADA:   'bg-blue-100 text-blue-700',
      RECHAZADA:  'bg-rose-100 text-rose-700',
      PENDIENTE:  'bg-amber-100 text-amber-700',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-600';
  }

  goBack(): void {
    this.location.back();
  }
}
