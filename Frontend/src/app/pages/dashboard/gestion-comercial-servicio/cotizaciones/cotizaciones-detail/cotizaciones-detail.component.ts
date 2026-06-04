import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CotizacionService, CotizacionReparacionOut, CotizacionRespuestaUpdate, CotizacionSolicitudCreate } from '../../../../../services/cotizacion.service';
import { AuthService } from '../../../../../core/services/auth.service';
import { Location } from '@angular/common';

@Component({
  selector: 'app-cotizaciones-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cotizaciones-detail.component.html',
  styleUrls: ['./cotizaciones-detail.component.css']
})
export class CotizacionesDetailComponent implements OnInit {
  idCotizacion: number | null = null;
  cotizacion: CotizacionReparacionOut | null = null;
  
  loading = false;
  error = '';
  esTaller = false;

  // Variables si hay repuesta
  precioEst = 0;
  detalleDanio = '';
  condiciones = '';
  tiempoEst = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
    private cotizacionService: CotizacionService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esTaller = rol === 'TALLER';

    this.route.paramMap.subscribe(params => {
      const idStr = params.get('id');
      if (idStr) {
        this.idCotizacion = +idStr;
        this.cargarCotizacion();
      }
    });
  }

  cargarCotizacion(): void {
    if (!this.idCotizacion) return;
    this.loading = true;
    this.cotizacionService.obtenerCotizacion(this.idCotizacion).subscribe({
      next: (data: CotizacionReparacionOut) => {
        this.cotizacion = data;
        if(this.cotizacion.precio_estimado) this.precioEst = this.cotizacion.precio_estimado;
        if(this.cotizacion.detalle_danio) this.detalleDanio = this.cotizacion.detalle_danio;
        if(this.cotizacion.condiciones_servicio) this.condiciones = this.cotizacion.condiciones_servicio;
        if(this.cotizacion.tiempo_estimado) this.tiempoEst = this.cotizacion.tiempo_estimado;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Error al cargar los detalles de la cotización';
        this.loading = false;
      }
    });
  }

  enviarRespuesta(): void {
    if(!this.idCotizacion) return;
    if(this.precioEst <= 0 || !this.detalleDanio || !this.condiciones || !this.tiempoEst) {
      alert("Comlete todos los campos de respuesta");
      return;
    }

    const payload: CotizacionRespuestaUpdate = {
      precio_estimado: this.precioEst,
      detalle_danio: this.detalleDanio,
      condiciones_servicio: this.condiciones,
      tiempo_estimado: this.tiempoEst
    };

    this.cotizacionService.responderCotizacion(this.idCotizacion, payload).subscribe({
      next: (res: CotizacionReparacionOut) => {
        this.cotizacion = res;
        alert("Cotización respondida correctamente");
      },
      error: (err: any) => {
        alert("Error al responder la cotización: " + (err.error?.detail || err.message));
      }
    });
  }

  goBack(): void {
    this.location.back();
  }
}
