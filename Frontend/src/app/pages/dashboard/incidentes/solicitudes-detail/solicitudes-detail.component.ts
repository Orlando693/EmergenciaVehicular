import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { TallerService } from '../../../../core/services/taller.service';
import { IncidenteOut } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-solicitudes-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-4xl mx-auto bg-white shadow rounded-lg p-6">
      <div class="flex items-center mb-6 border-b pb-4 gap-3">
        <button (click)="volver()" class="text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 p-2 rounded-full transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-2xl font-bold text-gray-800">Detalle de la Solicitud #{{ id() }}</h2>
      </div>

      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>

      <div *ngIf="solicitud() as sol" class="space-y-6">
        
        <!-- Header Info -->
        <div class="flex flex-col md:flex-row justify-between bg-red-50 border border-red-200 p-4 rounded-lg">
          <div>
            <p class="text-sm font-bold text-red-800">Clasificación IA / Tipo de Problema</p>
            <p class="text-xl font-bold text-gray-900 mt-1">{{ sol.clasificacion_ia || 'Asistencia Mecánica Requerida' }}</p>
            <div class="mt-2 flex gap-2">
              <span class="bg-red-600 text-white text-xs px-2 py-1 rounded shadow-sm font-bold tracking-wide">ALTA PRIORIDAD</span>
              <span class="bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-sm font-bold tracking-wide">{{ sol.estado }}</span>
            </div>
          </div>
          <div class="mt-4 md:mt-0 flex flex-col md:items-end justify-center">
            <p class="text-sm text-gray-500 font-medium">Hora del Reporte</p>
            <p class="font-semibold text-gray-800 mt-1"><i class="far fa-clock mr-1"></i>{{ sol.created_at | date:'HH:mm - dd/MM/yy' }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <!-- Ubicación  -->
          <div class="border rounded-lg p-5 bg-white shadow-sm">
            <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-map-marked-alt text-blue-600 mr-2"></i>Ubicación del Incidente</h3>
            <div class="space-y-3">
              <p class="text-gray-800 font-medium bg-gray-50 p-3 rounded border">{{ sol.direccion || 'Ubicación Desconocida' }}</p>
              
              <div *ngIf="sol.ubicacion_lat && sol.ubicacion_lng" class="flex items-center text-sm font-mono text-gray-500 bg-gray-50 p-2 rounded">
                <i class="fas fa-location-arrow mr-2"></i> Lat: {{ sol.ubicacion_lat | number:'1.4-4' }}, Lng: {{ sol.ubicacion_lng | number:'1.4-4' }}
              </div>
            </div>
          </div>

          <!-- Vehículo y Cliente -->
          <div class="border rounded-lg p-5 bg-white shadow-sm">
            <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-car-crash text-blue-600 mr-2"></i>Detalles del Vehículo</h3>
            <div class="space-y-4">
              <div class="bg-gray-50 p-3 rounded border flex flex-col gap-1 text-sm">
                 <p><span class="font-bold text-gray-600 w-20 inline-block">Placa:</span> <span class="bg-yellow-200 text-yellow-900 font-bold px-2 py-0.5 rounded">{{ sol.vehiculo_placa || 'N/A' }}</span></p>
                 <p><span class="font-bold text-gray-600 w-20 inline-block">Marca:</span> <span class="text-gray-800">{{ sol.vehiculo_marca || 'N/A' }}</span></p>
                 <p><span class="font-bold text-gray-600 w-20 inline-block">Modelo:</span> <span class="text-gray-800">{{ sol.vehiculo_modelo || 'N/A' }}</span></p>
              </div>
            </div>
          </div>

        </div>

        <!-- Descripción Completa -->
        <div class="border rounded-lg p-5 shadow-sm">
           <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-comment-dots text-blue-600 mr-2"></i>Descripción del Reporte</h3>
           
           <div class="bg-blue-50 border border-blue-200 p-4 rounded text-blue-900 whitespace-pre-wrap leading-relaxed shadow-inner">
             "{{ sol.descripcion }}"
           </div>
           
           <div class="flex gap-4 mt-4">
             <a *ngIf="sol.imagen_url" [href]="sol.imagen_url" target="_blank" class="flex-1 flex max-w-48 items-center justify-center p-3 border rounded bg-gray-50 hover:bg-gray-100 text-gray-700 hover:text-blue-800 transition shadow-sm font-medium text-sm">
               <i class="fas fa-image mr-2 text-lg"></i> Ver Imagen
             </a>
             <a *ngIf="sol.audio_url" [href]="sol.audio_url" target="_blank" class="flex-1 flex max-w-48 items-center justify-center p-3 border rounded bg-gray-50 hover:bg-gray-100 text-gray-700 hover:text-blue-800 transition shadow-sm font-medium text-sm">
               <i class="fas fa-play-circle mr-2 text-lg"></i> Escuchar Audio
             </a>
           </div>
        </div>

      </div>
    </div>
  `
})
export class SolicitudesDetailComponent implements OnInit {
  private tallerService = inject(TallerService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  id = signal<number | null>(null);
  solicitud = signal<IncidenteOut | null>(null);
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

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
      next: (data) => {
        this.solicitud.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set('No se pudieron cargar los detalles de esta solicitud o ya no está disponible.');
        this.cargando.set(false);
      }
    });
  }

  volver() {
    this.router.navigate(['/dashboard/solicitudes-disponibles']);
  }
}
