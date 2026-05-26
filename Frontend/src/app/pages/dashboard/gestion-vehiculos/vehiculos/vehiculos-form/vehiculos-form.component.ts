import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { VehiculoService, VehiculoUpdate } from '../../../../../core/services/vehiculo.service';

@Component({
  selector: 'app-vehiculos-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="max-w-2xl mx-auto bg-white shadow rounded-lg p-6">
      <div class="flex items-center mb-6 gap-3">
        <button (click)="volver()" class="text-gray-500 hover:text-gray-700">
          <i class="fas fa-arrow-left text-xl"></i>
        </button>
        <h2 class="text-2xl font-bold text-gray-800">{{ esEdicion() ? 'Editar Vehículo' : 'Registrar Nuevo Vehículo' }}</h2>
      </div>

      <div *ngIf="error()" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
        {{ error() }}
      </div>

      <form [formGroup]="vehiculoForm" (ngSubmit)="guardar()">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <!-- Placa -->
          <div class="col-span-1 md:col-span-2">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="placa">Placa (Matrícula) *</label>
            <input formControlName="placa" id="placa" type="text" placeholder="ABC-1234" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase">
            <div *ngIf="vehiculoForm.get('placa')?.touched && vehiculoForm.get('placa')?.invalid" class="text-red-500 text-xs mt-1">Placa es obligatoria.</div>
          </div>

          <!-- Marca -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Marca *</label>
            <input formControlName="marca" type="text" placeholder="Ej. Toyota, Nissan" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
            <div *ngIf="vehiculoForm.get('marca')?.touched && vehiculoForm.get('marca')?.invalid" class="text-red-500 text-xs mt-1">Marca requerida.</div>
          </div>

          <!-- Modelo -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Modelo *</label>
            <input formControlName="modelo" type="text" placeholder="Ej. Corolla" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
            <div *ngIf="vehiculoForm.get('modelo')?.touched && vehiculoForm.get('modelo')?.invalid" class="text-red-500 text-xs mt-1">Modelo requerido.</div>
          </div>

          <!-- Año -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Año</label>
            <input formControlName="anio" type="number" placeholder="Ej. 2020" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <!-- Color -->
          <div>
            <label class="block text-gray-700 text-sm font-bold mb-2">Color</label>
            <input formControlName="color" type="text" placeholder="Ej. Rojo" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <!-- VIN -->
          <div class="col-span-1 md:col-span-2">
            <label class="block text-gray-700 text-sm font-bold mb-2">VIN (Opcional)</label>
            <input formControlName="vin" type="text" placeholder="Número de chasis" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <!-- Activo (Solo edición) -->
          <div *ngIf="esEdicion()" class="col-span-1 md:col-span-2 pt-2 border-t mt-2">
            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="checkbox" formControlName="activo" class="form-checkbox h-5 w-5 text-blue-600 rounded">
              <span class="text-gray-700 font-medium">Vehículo activo</span>
            </label>
          </div>
        </div>

        <div class="flex items-center justify-end mt-6 gap-4 border-t pt-4">
          <button type="button" (click)="volver()" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
            Cancelar
          </button>
          <button type="submit" [disabled]="vehiculoForm.invalid || guardando()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center disabled:opacity-50">
            <i class="fas fa-spinner fa-spin mr-2" *ngIf="guardando()"></i>
            {{ esEdicion() ? 'Actualizar Vehículo' : 'Guardar Vehículo' }}
          </button>
        </div>
      </form>
    </div>
  `
})
export class VehiculosFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private vehiculoService = inject(VehiculoService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  vehiculoForm!: FormGroup;
  idVehiculo = signal<number | null>(null);
  esEdicion = signal<boolean>(false);
  guardando = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.vehiculoForm = this.fb.group({
      placa: ['', [Validators.required, Validators.maxLength(20)]],
      marca: ['', [Validators.required, Validators.maxLength(80)]],
      modelo: ['', [Validators.required, Validators.maxLength(80)]],
      anio: [null, [Validators.min(1900), Validators.max(new Date().getFullYear() + 1)]],
      color: ['', [Validators.maxLength(50)]],
      vin: ['', [Validators.maxLength(50)]],
      activo: [true]
    });

    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.esEdicion.set(true);
      this.idVehiculo.set(Number(idParam));
      this.cargarVehiculo();
    }
  }

  cargarVehiculo() {
    this.vehiculoService.obtenerVehiculo(this.idVehiculo()!).subscribe({
      next: (vehiculo) => {
        this.vehiculoForm.patchValue({
          placa: vehiculo.placa,
          marca: vehiculo.marca,
          modelo: vehiculo.modelo,
          anio: vehiculo.anio,
          color: vehiculo.color,
          vin: vehiculo.vin,
          activo: vehiculo.activo
        });
      },
      error: () => this.error.set('No se pudo cargar el vehículo.')
    });
  }

  guardar() {
    if (this.vehiculoForm.invalid) {
      this.vehiculoForm.markAllAsTouched();
      return;
    }

    this.guardando.set(true);
    this.error.set(null);

    const datos = { ...this.vehiculoForm.value };
    datos.placa = datos.placa.toUpperCase();

    if (this.esEdicion()) {
      this.vehiculoService.actualizarVehiculo(this.idVehiculo()!, datos as VehiculoUpdate).subscribe({
        next: () => {
          this.guardando.set(false);
          this.volver();
        },
        error: (err) => {
          this.guardando.set(false);
          this.error.set(err.error?.detail || 'Error al actualizar el vehículo (posible placa duplicada).');
        }
      });
    } else {
      // Eliminar el campo activo ya que solo se envia en updates
      delete datos.activo;
      this.vehiculoService.registrarVehiculo(datos).subscribe({
        next: () => {
          this.guardando.set(false);
          this.volver();
        },
        error: (err) => {
          this.guardando.set(false);
          this.error.set(err.error?.detail || 'Error al registrar el vehículo (verifique la placa).');
        }
      });
    }
  }

  volver() {
    this.router.navigate(['/dashboard/vehiculos']);
  }
}
