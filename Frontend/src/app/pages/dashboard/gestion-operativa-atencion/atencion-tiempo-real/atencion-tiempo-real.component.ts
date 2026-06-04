import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AtencionTiempoRealService, AtencionSeguimientoOut, AtencionEventoOut } from '../../../../services/atencion-tiempo-real.service';
import { AuthService } from '../../../../core/services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-atencion-tiempo-real',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './atencion-tiempo-real.component.html',
  styleUrls: ['./atencion-tiempo-real.component.css']
})
export class AtencionTiempoRealComponent implements OnInit, OnDestroy {
  idIncidente!: number;
  seguimiento: AtencionSeguimientoOut | null = null;
  loading = true;
  error = '';
  nuevoEstado = '';
  observacion = '';
  roles: string[] = [];
  esTaller = false;
  esCliente = false;
  wsSubscription!: Subscription;

  estadosPermitidos = ['EN_PROCESO', 'RESUELTO', 'CANCELADO']; // Taller can select
  
  constructor(
    private route: ActivatedRoute,
    private atencionService: AtencionTiempoRealService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esTaller = rol === 'TALLER';
    this.esCliente = rol === 'CLIENTE';
    
    // Si tenemos un estado centralizado del usuario
    const token = this.authService.getToken() || '';

    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.idIncidente = +id;
        this.cargarSeguimiento();
        if (token) {
          this.atencionService.conectarWebSocket(this.idIncidente, token);
        }
      }
    });

    this.wsSubscription = this.atencionService.eventos$.subscribe(evento => {
      console.log('Evento en tiempo real:', evento);
      if (evento.tipo === 'SEGUIMIENTO_INICIAL') {
        this.seguimiento = evento.data;
      } else if (evento.tipo === 'UPDATE_ESTADO' || evento.tipo === 'EVENTO_NUEVO') {
        // Recargar el seguimiento completo ante cualquier cambio
        this.cargarSeguimiento();
      }
    });
  }

  cargarSeguimiento(): void {
    this.loading = true;
    this.atencionService.obtenerSeguimiento(this.idIncidente).subscribe({
      next: (data) => {
        this.seguimiento = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar la atención del incidente';
        this.loading = false;
      }
    });
  }

  aceptar(): void {
    this.atencionService.aceptarAtencion(this.idIncidente, this.observacion).subscribe({
      next: () => {
        this.observacion = '';
        this.cargarSeguimiento();
      },
      error: (err) => {
        alert('Error al aceptar la atención: ' + (err.error?.detail || err.message));
      }
    });
  }

  rechazar(): void {
    this.atencionService.rechazarAtencion(this.idIncidente, this.observacion).subscribe({
      next: () => {
        this.observacion = '';
        this.cargarSeguimiento();
      },
      error: (err) => {
        alert('Error al rechazar la atención: ' + (err.error?.detail || err.message));
      }
    });
  }

  actualizarEstado(): void {
    if (!this.nuevoEstado) {
      alert('Debe seleccionar un estado.');
      return;
    }
    this.atencionService.actualizarEstado(this.idIncidente, this.nuevoEstado, this.observacion).subscribe({
      next: () => {
        this.nuevoEstado = '';
        this.observacion = '';
        this.cargarSeguimiento();
      },
      error: (err) => {
        alert('Error al actualizar el estado: ' + (err.error?.detail || err.message));
      }
    });
  }

  ngOnDestroy(): void {
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
    }
    this.atencionService.desconectarWebSocket();
  }
}