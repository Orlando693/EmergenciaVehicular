import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../core/services/incidente.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-incidentes-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-4xl mx-auto bg-white shadow rounded-lg p-6">
      <div class="flex items-center mb-6 gap-3 border-b pb-4">
        <button (click)="volver()" class="text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 p-2 rounded-full transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-2xl font-bold text-gray-800">Detalle del Incidente #{{ id() }}</h2>
      </div>

      <!-- Loading State -->
      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Errors and Success -->
      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>
      <div *ngIf="successMsg()" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4">
        <i class="fas fa-check-circle mr-2"></i>{{ successMsg() }}
      </div>

      <div *ngIf="incidente() as inc" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Main Form Left Side -->
        <div class="lg:col-span-2 space-y-6">
           <div class="flex flex-col md:flex-row justify-between bg-gray-50 p-4 rounded-lg border">
             <div>
               <p class="text-sm text-gray-500 font-medium">Estado Actual</p>
               <span class="px-3 py-1 inline-flex text-sm leading-5 font-bold rounded-full mt-1"
                     [ngClass]="{
                       'bg-yellow-100 text-yellow-800': inc.estado === 'REPORTADO',
                       'bg-blue-100 text-blue-800': inc.estado === 'EN_PROCESO',
                       'bg-green-100 text-green-800': inc.estado === 'RESUELTO',
                       'bg-red-100 text-red-800': inc.estado === 'CANCELADO'
                     }">
                 {{ inc.estado }}
               </span>
             </div>
             <div class="mt-4 md:mt-0 md:text-right">
               <p class="text-sm text-gray-500 font-medium">Fecha Reporte</p>
               <p class="font-semibold text-gray-800 mt-1">{{ inc.created_at | date:'medium' }}</p>
             </div>
           </div>

           <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
             <!-- Vehiculo Info -->
             <div class="border rounded-lg p-5">
               <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-car text-blue-600 mr-2"></i>Vehículo Afectado</h3>
               <div class="space-y-2">
                 <p><span class="font-medium text-gray-600">Placa:</span> <span class="bg-yellow-100 text-yellow-800 px-2 rounded">{{ inc.vehiculo_placa || 'Desconocida' }}</span></p>
                 <p><span class="font-medium text-gray-600">Modelo:</span> {{ inc.vehiculo_marca }} {{ inc.vehiculo_modelo }}</p>
               </div>
             </div>

             <!-- Taller Info (CU12) -->
             <div class="border rounded-lg p-5 flex flex-col justify-between" [ngClass]="{'bg-green-50 border-green-200': inc.id_taller, 'bg-yellow-50 border-yellow-200': !inc.id_taller}">
               <div>
                 <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-wrench text-blue-600 mr-2"></i>Asignación</h3>
                 <div *ngIf="inc.id_taller">
                   <p><span class="font-medium text-gray-600">Taller Asignado:</span></p>
                   <p class="text-xl font-bold text-green-800 py-1 break-words"><i class="fas fa-check text-green-600 mr-2"></i>{{ inc.taller_nombre }}</p>
                 </div>
                 <div *ngIf="!inc.id_taller" class="text-yellow-700 flex items-center mb-3 font-medium">
                   <i class="fas fa-clock mr-2"></i> A la espera de asignación de taller óptimo (Automático por el Sistema).
                 </div>
               </div>

               <!-- Boton simular CU12 - Solo Admin o Sistema -->
               <div *ngIf="!inc.id_taller && auth.rol === 'ADMINISTRADOR'" class="mt-4 border-t border-yellow-300 pt-3">
                  <button (click)="asignarTaller()" [disabled]="asignando()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded focus:outline-none transition flex justify-center items-center gap-2">
                    <i class="fas" [ngClass]="{'fa-magic': !asignando(), 'fa-spinner fa-spin': asignando()}"></i>
                    {{ asignando() ? 'El Sistema está evaluando...' : 'Simular Asignación del Sistema (CU12)' }}
                  </button>
               </div>
             </div>
           </div>

           <!-- AI Details -->
           <div class="border rounded-lg p-5 bg-indigo-50 border-indigo-200">
             <h3 class="text-lg font-bold border-b border-indigo-200 pb-2 mb-3 text-indigo-900"><i class="fas fa-robot text-indigo-600 mr-2"></i>Análisis de Inteligencia Artificial</h3>
             <div class="mb-4">
               <p class="text-sm font-bold text-indigo-800 mb-1">Clasificación:</p>
               <span class="bg-indigo-600 text-white px-3 py-1 rounded shadow-sm text-sm font-medium">{{ inc.clasificacion_ia || 'Pendiente' }}</span>
             </div>
             <div>
               <p class="text-sm font-bold text-indigo-800 mb-1">Resumen del IA:</p>
               <p class="text-indigo-900 bg-white p-3 rounded border border-indigo-100 text-sm leading-relaxed whitespace-pre-wrap">{{ inc.resumen_ia || 'Sin resumen disponible aún.' }}</p>
             </div>
           </div>

           <!-- User Original Report -->
           <div class="border rounded-lg p-5">
              <h3 class="text-lg font-bold border-b pb-2 mb-3 text-gray-800"><i class="fas fa-file-alt text-blue-600 mr-2"></i>Reporte Original</h3>
              <div class="mb-4">
                <p class="text-sm text-gray-500 font-medium mb-1">Descripción del Cliente:</p>
                <p class="text-gray-800 bg-gray-50 p-3 rounded text-sm italic border">" {{ inc.descripcion }} "</p>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div *ngIf="inc.direccion" class="bg-gray-50 p-3 rounded border">
                   <p class="text-xs text-gray-500 font-bold mb-1"><i class="fas fa-map-marker-alt mr-1"></i>Dirección / Ubicación</p>
                   <p class="text-sm text-gray-800">{{ inc.direccion }}</p>
                </div>
                <div class="flex gap-3">
                  <a *ngIf="inc.imagen_url" [href]="inc.imagen_url" target="_blank" class="flex-1 flex flex-col items-center justify-center p-3 border rounded-lg bg-gray-50 hover:bg-gray-100 text-blue-600 hover:text-blue-800 transition">
                    <i class="fas fa-image text-2xl mb-1"></i>
                    <span class="text-xs font-bold">Ver Imagen</span>
                  </a>
                  <a *ngIf="inc.audio_url" [href]="inc.audio_url" target="_blank" class="flex-1 flex flex-col items-center justify-center p-3 border rounded-lg bg-gray-50 hover:bg-gray-100 text-blue-600 hover:text-blue-800 transition">
                    <i class="fas fa-play-circle text-2xl mb-1"></i>
                    <span class="text-xs font-bold">Oír Audio</span>
                  </a>
                </div>
              </div>
           </div>
        </div>

        <!-- Right Side: Sidebar History (CU13) - Only Client/Admin Reading -->
        <div class="lg:col-span-1">
           <div class="border rounded-lg p-4 bg-gray-50 h-full">
              <h3 class="text-gray-800 font-bold mb-4 border-b pb-2"><i class="fas fa-history text-blue-600 mr-2"></i>Historial del Servicio</h3>
              
              <div *ngIf="cargandoHistorial()" class="text-center py-4 text-gray-500">
                 <i class="fas fa-spinner fa-spin mr-2"></i> Cargando...
              </div>

              <div class="relative space-y-4" *ngIf="!cargandoHistorial() && historialEstados().length > 0">
                 <div *ngFor="let hist of historialEstados(); let isLast = last" class="relative pl-6">
                    <div class="absolute left-0 top-1.5 w-2 h-2 rounded-full ring-4 ring-white"
                         [ngClass]="{
                           'bg-yellow-400': hist.estado_nuevo === 'REPORTADO',
                           'bg-blue-400': hist.estado_nuevo === 'EN_PROCESO',
                           'bg-green-400': hist.estado_nuevo === 'RESUELTO',
                           'bg-red-400': hist.estado_nuevo === 'CANCELADO'
                         }"></div>
                    <div *ngIf="!isLast" class="absolute left-1 top-3.5 w-0.5 h-full bg-gray-200"></div>
                    
                    <p class="text-xs text-gray-500 font-medium">{{ hist.created_at | date:'short' }}</p>
                    <p class="text-sm font-bold text-gray-800">
                       <span *ngIf="hist.estado_anterior" class="text-gray-400 font-normal mr-1">{{ hist.estado_anterior }} &rarr;</span>
                       {{ hist.estado_nuevo }}
                    </p>
                    <p *ngIf="hist.observacion" class="text-xs text-gray-600 bg-white border p-1.5 mt-1 rounded italic">"{{ hist.observacion }}"</p>
                 </div>
              </div>

              <div *ngIf="!cargandoHistorial() && historialEstados().length === 0" class="text-sm text-gray-500 text-center mt-4">
                 No hay cambios de estado aún.
              </div>
           </div>
        </div>
      </div>
    </div>
  `
})
export class IncidentesDetailComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private incidenteService = inject(IncidenteService);
  public auth = inject(AuthService);

  id = signal<number | null>(null);
  incidente = signal<IncidenteOut | null>(null);
  historialEstados = signal<any[]>([]);
  
  cargando = signal<boolean>(false);
  cargandoHistorial = signal<boolean>(false);
  asignando = signal<boolean>(false);
  
  error = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.id.set(Number(idParam));
      this.cargarIncidente();
      this.cargarHistorial();
    }
  }

  cargarIncidente() {
    this.cargando.set(true);
    this.error.set(null);
    this.incidenteService.obtenerDetalle(this.id()!).subscribe({
      next: (data) => {
        this.incidente.set(data);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo encontrar el detalle de este incidente.');
        this.cargando.set(false);
      }
    });
  }

  cargarHistorial() {
    this.cargandoHistorial.set(true);
    this.incidenteService.consultarHistorialEstados(this.id()!).subscribe({
      next: (data) => {
        this.historialEstados.set(data);
        this.cargandoHistorial.set(false);
      },
      error: () => {
        this.cargandoHistorial.set(false);
      }
    });
  }

  asignarTaller() {
    if (!this.id()) return;
    this.asignando.set(true);
    this.error.set(null);
    this.successMsg.set(null);

    this.incidenteService.asignarTaller(this.id()!).subscribe({
      next: (data) => {
        this.incidente.set(data);
        this.successMsg.set('El sistema ha encontrado y asignado el taller óptimo exitosamente.');
        this.cargarHistorial();
        this.asignando.set(false);
      },
      error: (err) => {
         this.error.set(err?.error?.detail || 'No se pudo asignar el taller automáticamente. ¿Existen talleres disponibles?');
         this.asignando.set(false);
      }
    });
  }

  volver() {
    this.router.navigate(['/dashboard/incidentes']);
  }
}
