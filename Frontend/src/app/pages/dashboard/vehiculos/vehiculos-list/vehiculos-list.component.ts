import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { VehiculoService, Vehiculo } from '../../../../core/services/vehiculo.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-vehiculos-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bg-white shadow rounded-lg p-6">
      <div class="flex justify-between items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Mis Vehículos</h2>
        <button (click)="nuevoVehiculo()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow flex items-center gap-2">
          <i class="fas fa-plus"></i> Registrar Vehículo
        </button>
      </div>

      <!-- Loading State -->
      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Error State -->
      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>

      <!-- Empty State -->
      <div *ngIf="!cargando() && vehiculos().length === 0" class="text-center p-8 border-2 border-dashed border-gray-300 rounded-lg">
        <i class="fas fa-car text-4xl text-gray-400 mb-4"></i>
        <h3 class="text-lg font-medium text-gray-900">No tienes vehículos registrados</h3>
        <p class="mt-1 text-gray-500">Registra un vehículo para solicitar asistencia.</p>
        <button (click)="nuevoVehiculo()" class="mt-4 text-blue-600 hover:underline">Registrar ahora</button>
      </div>

      <!-- Grid de Vehículos -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" *ngIf="!cargando() && vehiculos().length > 0">
        <div *ngFor="let vehiculo of vehiculos()" class="border rounded-lg p-4 shadow-sm hover:shadow-md transition relative bg-gray-50">
          <div class="flex justify-between items-start mb-2">
            <h3 class="text-xl font-bold text-gray-800">{{ vehiculo.marca }} {{ vehiculo.modelo }}</h3>
            <span [class]="vehiculo.activo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="text-xs px-2 py-1 rounded-full font-semibold">
              {{ vehiculo.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
          
          <div class="space-y-2 mb-4 text-sm text-gray-600">
            <p><span class="font-medium">Placa:</span> <span class="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">{{ vehiculo.placa }}</span></p>
            <p><span class="font-medium">Año:</span> {{ vehiculo.anio || 'N/A' }}</p>
            <p><span class="font-medium">Color:</span> {{ vehiculo.color || 'N/A' }}</p>
          </div>

          <div class="flex gap-2">
            <button (click)="editarVehiculo(vehiculo.id_vehiculo)" class="w-full text-center bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-2 rounded text-sm transition">
              <i class="fas fa-edit mr-1"></i> Editar
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class VehiculosListComponent implements OnInit {
  private vehiculoService = inject(VehiculoService);
  private router = inject(Router);
  public authService = inject(AuthService); // Permisos de UI si requiere Admin/Cliente

  vehiculos = signal<Vehiculo[]>([]);
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.cargarVehiculos();
  }

  cargarVehiculos() {
    this.cargando.set(true);
    this.error.set(null);
    this.vehiculoService.consultarVehiculos().subscribe({
      next: (data) => {
        this.vehiculos.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set('Error al cargar la lista de vehículos.');
        this.cargando.set(false);
      }
    });
  }

  nuevoVehiculo() {
    this.router.navigate(['/dashboard/vehiculos/nuevo']);
  }

  editarVehiculo(id: number) {
    this.router.navigate([`/dashboard/vehiculos/editar`, id]);
  }
}
