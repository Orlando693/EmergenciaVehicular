import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CotizacionService, CotizacionReparacionOut } from '../../../../../services/cotizacion.service';
import { AuthService } from '../../../../../core/services/auth.service';

@Component({
  selector: 'app-cotizaciones-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './cotizaciones-list.component.html',
  styleUrls: ['./cotizaciones-list.component.css']
})
export class CotizacionesListComponent implements OnInit {
  cotizaciones: CotizacionReparacionOut[] = [];
  loading = true;
  error = '';
  esCliente = false;

  constructor(
    private cotizacionService: CotizacionService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esCliente = rol === 'CLIENTE';
    this.cargarCotizaciones();
  }

  cargarCotizaciones(): void {
    this.loading = true;
    this.cotizacionService.listarCotizaciones().subscribe({
      next: (data: CotizacionReparacionOut[]) => {
        this.cotizaciones = data;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Error al cargar las cotizaciones';
        this.loading = false;
      }
    });
  }
}
