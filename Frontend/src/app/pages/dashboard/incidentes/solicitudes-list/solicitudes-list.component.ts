import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TallerService } from '../../../../core/services/taller.service';
import { IncidenteOut } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-solicitudes-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white shadow rounded-lg p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-800"><i class="fas fa-satellite-dish text-blue-600 mr-2"></i>Solicitudes Disponibles</h2>
      </div>

      <!-- Estado de Carga -->
      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Estado de Error -->
      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>

      <!-- Estado Vacío -->
      <div *ngIf="!cargando() && solicitudes().length === 0" class="text-center p-10 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
        <i class="fas fa-check-circle text-5xl text-green-400 mb-4 block"></i>
        <h3 class="text-xl font-medium text-gray-900">No hay nuevas solicitudes</h3>
        <p class="mt-2 text-gray-500">Por el momento no hay incidentes pendientes de asistencia o fuera de tu zona de cobertura.</p>
        <button (click)="cargarSolicitudes()" class="mt-4 text-blue-600 hover:text-blue-800 font-medium">
          <i class="fas fa-sync-alt mr-1"></i> Actualizar Listado
        </button>
      </div>

      <!-- Listado (Tarjetas o Tabla) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" *ngIf="!cargando() && solicitudes().length > 0">
        <div *ngFor="let sol of solicitudes()" class="bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden flex flex-col">
          <div class="bg-red-50 border-b border-red-100 p-4 shrink-0">
             <div class="flex justify-between items-start">
               <span class="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">Prioridad Alta</span>
               <span class="text-xs font-medium text-gray-500">{{ sol.created_at | date:'shortTime' }}</span>
             </div>
             <h3 class="text-lg font-bold text-gray-900 mt-2 truncate">{{ sol.clasificacion_ia || 'Problema Vehicular' }}</h3>
          </div>
          
          <div class="p-4 flex-grow">
            <p class="text-sm text-gray-600 mb-3 line-clamp-2">"{{ sol.descripcion }}"</p>
            <div class="flex items-center text-sm text-gray-700 mb-2">
              <i class="fas fa-map-marker-alt text-gray-400 w-5"></i> 
              <span class="truncate">{{ sol.direccion || 'Ubicación GPS' }}</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <i class="fas fa-car text-gray-400 w-5"></i> 
              <span class="truncate">{{ sol.vehiculo_marca || 'Vehículo' }} {{ sol.vehiculo_modelo || 'Afectado' }}</span>
            </div>
          </div>
          
          <div class="bg-gray-50 p-4 border-t flex justify-end shrink-0">
            <button (click)="verDetalle(sol.id_incidente)" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition">
              Ver Detalles
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class SolicitudesListComponent implements OnInit {
  private tallerService = inject(TallerService);
  private router = inject(Router);

  solicitudes = signal<IncidenteOut[]>([]);
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.cargarSolicitudes();
  }

  cargarSolicitudes() {
    this.cargando.set(true);
    this.error.set(null);
    this.tallerService.solicitudesDisponibles().subscribe({
      next: (data) => {
        this.solicitudes.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set('Error al cargar las solicitudes. Intente nuevamente.');
        this.cargando.set(false);
      }
    });
  }

  verDetalle(id: number) {
    this.router.navigate(['/dashboard/solicitudes-disponibles/detalle', id]);
  }
}
