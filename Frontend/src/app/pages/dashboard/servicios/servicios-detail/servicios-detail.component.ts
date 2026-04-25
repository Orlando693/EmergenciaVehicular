import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { IncidenteService, IncidenteOut } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-servicios-detail',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="max-w-4xl mx-auto bg-white shadow rounded-lg p-6">
      <div class="flex items-center mb-6 gap-3 border-b pb-4">
        <button (click)="volver()" class="text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 p-2 rounded-full transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-2xl font-bold text-gray-800">Atención del Servicio #{{ id() }}</h2>
      </div>

      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>
      <div *ngIf="successMsg()" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4">
        <i class="fas fa-check-circle mr-2"></i>{{ successMsg() }}
      </div>

      <div *ngIf="solicitud() as sol" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- MAIN INCIDENT DETAILS -->
        <div class="lg:col-span-2 space-y-5">
           <!-- Header Status -->
           <div class="bg-blue-50 border border-blue-200 p-4 rounded-lg flex justify-between items-center">
             <div>
                <p class="text-sm font-bold text-blue-800 uppercase tracking-widest">Estado del Servicio</p>
                <span class="mt-1 px-3 py-1 inline-flex text-sm leading-5 font-bold rounded-full"
                      [ngClass]="{
                        'bg-yellow-100 text-yellow-800': sol.estado === 'REPORTADO',
                        'bg-blue-100 text-blue-800': sol.estado === 'EN_PROCESO',
                        'bg-green-100 text-green-800': sol.estado === 'RESUELTO',
                        'bg-red-100 text-red-800': sol.estado === 'CANCELADO'
                      }">
                  {{ sol.estado }}
                </span>
             </div>
             <div class="text-right">
                <p class="text-xs text-gray-500"><i class="fas fa-calendar mr-1"></i> Asignado el</p>
                <p class="font-bold text-gray-800">{{ sol.created_at | date:'shortDate' }}</p>
             </div>
           </div>

           <!-- Client Problem -->
           <div class="border rounded-lg p-5 bg-white shadow-sm">
              <h3 class="text-gray-800 font-bold mb-3 border-b pb-2"><i class="fas fa-wrench text-blue-600 mr-2"></i>Problema Reportado</h3>
              <p class="text-gray-800 text-sm font-medium mb-1"><span class="text-gray-500">IA Clasificó:</span> {{ sol.clasificacion_ia }}</p>
              <div class="bg-gray-50 border p-3 rounded text-gray-700 text-sm italic mb-3">
                 "{{ sol.descripcion }}"
              </div>
              <p class="text-sm text-gray-800 bg-gray-100 p-2 rounded"><i class="fas fa-map-marker-alt text-red-500 mr-2"></i>{{ sol.direccion }}</p>
           </div>

           <!-- Update State Form (CU13) -->
           <div class="border border-blue-200 rounded-lg p-5 bg-blue-50 shadow-sm relative">
              <h3 class="text-blue-900 font-bold mb-3 border-b border-blue-200 pb-2"><i class="fas fa-edit mr-2"></i>Actualizar Estado</h3>
              
              <form [formGroup]="estadoForm" (ngSubmit)="actualizarEstado()">
                 <div class="mb-3">
                    <label class="block text-gray-700 text-sm font-bold mb-2">Nuevo Estado</label>
                    <select formControlName="estado" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
                       <option value="" disabled selected>Seleccione estado...</option>
                       <option value="EN_PROCESO">En Proceso</option>
                       <option value="RESUELTO">Finalizado / Resuelto</option>
                       <option value="CANCELADO">Cancelado</option>
                    </select>
                 </div>
                 <div class="mb-3">
                    <label class="block text-gray-700 text-sm font-bold mb-2">Observaciones / Notas (Opcional)</label>
                    <textarea formControlName="observacion" rows="2" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ej. El técnico ya está en ruta..."></textarea>
                 </div>
                 <button type="submit" [disabled]="estadoForm.invalid || actualizando()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition flex justify-center items-center disabled:opacity-50">
                    <i class="fas" [ngClass]="{'fa-save': !actualizando(), 'fa-spinner fa-spin': actualizando()}"></i>
                    <span class="ml-2">Registrar Cambio de Estado</span>
                 </button>
              </form>
           </div>
        </div>

        <!-- SIDEBAR HISTORY -->
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
export class ServiciosDetailComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private incidenteService = inject(IncidenteService);

  id = signal<number | null>(null);
  solicitud = signal<IncidenteOut | null>(null);
  historialEstados = signal<any[]>([]);
  
  cargando = signal<boolean>(false);
  cargandoHistorial = signal<boolean>(false);
  actualizando = signal<boolean>(false);

  error = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  estadoForm: FormGroup;

  constructor() {
    this.estadoForm = this.fb.group({
      estado: ['', Validators.required],
      observacion: ['']
    });
  }

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.id.set(Number(idParam));
      this.cargarServicio();
      this.cargarHistorial();
    }
  }

  cargarServicio() {
    this.cargando.set(true);
    this.incidenteService.obtenerDetalle(this.id()!).subscribe({
      next: (data) => {
        this.solicitud.set(data);
        this.estadoForm.patchValue({ estado: data.estado });
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo encontrar el detalle de este servicio.');
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

  actualizarEstado() {
    if (this.estadoForm.invalid) return;

    this.actualizando.set(true);
    this.error.set(null);
    this.successMsg.set(null);

    const payload = this.estadoForm.value;

    this.incidenteService.actualizarEstado(this.id()!, payload).subscribe({
      next: (updatedSol) => {
        this.successMsg.set('Estado y observaciones actualizadas exitosamente.');
        this.solicitud.set(updatedSol);
        this.cargarHistorial(); 
        this.actualizando.set(false);
        this.estadoForm.patchValue({ observacion: '' }); // Clear observation after success
      },
      error: (err) => {
         this.error.set(err?.error?.detail || 'Error al actualizar el estado del servicio.');
         this.actualizando.set(false);
      }
    });
  }

  volver() {
    this.router.navigate(['/dashboard/servicios']);
  }
}
