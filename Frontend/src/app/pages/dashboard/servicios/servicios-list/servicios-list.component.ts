import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { IncidenteService, IncidenteOut } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-servicios-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white shadow rounded-lg p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-800"><i class="fas fa-list-alt text-blue-600 mr-2"></i>Mis Servicios Asignados</h2>
      </div>

      <div *ngIf="cargando()" class="flex justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>

      <div *ngIf="!cargando() && incidentes().length === 0" class="text-center p-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
        <i class="fas fa-folder-open text-4xl text-gray-400 mb-4"></i>
        <h3 class="text-lg font-medium text-gray-900">No hay servicios asignados</h3>
        <p class="mt-1 text-gray-500">Aún no tienes incidentes asignados a este taller.</p>
      </div>

      <div class="overflow-x-auto" *ngIf="!cargando() && incidentes().length > 0">
        <table class="min-w-full bg-white divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clasificación IA</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vehículo</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr *ngFor="let inc of incidentes()" class="hover:bg-gray-50 transition">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ inc.created_at | date:'short' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                {{ inc.clasificacion_ia || 'Sin Clasificar' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ inc.vehiculo_marca }} {{ inc.vehiculo_modelo }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      [ngClass]="{
                        'bg-yellow-100 text-yellow-800': inc.estado === 'REPORTADO',
                        'bg-blue-100 text-blue-800': inc.estado === 'EN_PROCESO',
                        'bg-green-100 text-green-800': inc.estado === 'RESUELTO',
                        'bg-red-100 text-red-800': inc.estado === 'CANCELADO'
                      }">
                  {{ inc.estado }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button (click)="verDetalle(inc.id_incidente)" class="text-white bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded transition">
                  <i class="fas fa-eye mr-1"></i> Gestionar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `
})
export class ServiciosListComponent implements OnInit {
  private router = inject(Router);
  private incidenteService = inject(IncidenteService);

  incidentes = signal<IncidenteOut[]>([]);
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.cargarHistorial();
  }

  cargarHistorial() {
    this.cargando.set(true);
    this.incidenteService.consultarHistorial().subscribe({
      next: (data) => {
        this.incidentes.set(data);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('Error al cargar la lista de servicios asignados.');
        this.cargando.set(false);
      }
    });
  }

  verDetalle(id: number) {
    this.router.navigate(['/dashboard/servicios/detalle', id]);
  }
}
