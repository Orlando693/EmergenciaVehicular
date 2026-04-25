import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { VehiculoService, Vehiculo } from '../../../../core/services/vehiculo.service';
import { IncidenteService, IncidenteCreate } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-incidentes-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './incidentes-form.component.html',
  styleUrl: './incidentes-form.component.css'
})
export class IncidentesFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private vehiculoService = inject(VehiculoService);
  private incidenteService = inject(IncidenteService);

  incidenteForm!: FormGroup;
  vehiculos = signal<Vehiculo[]>([]);
  
  cargandoVehiculos = signal(true);
  procesando = signal(false);
  
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);
  
  latitud = signal<number | null>(null);
  longitud = signal<number | null>(null);

  ngOnInit() {
    this.initForm();
    this.cargarVehiculos();
  }

  initForm() {
    this.incidenteForm = this.fb.group({
      id_vehiculo: ['', Validators.required],
      descripcion: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(1000)]],
      direccion: ['', Validators.required],
      imagen_url: [''],
      audio_url: ['']
    });
  }

  get f() { return this.incidenteForm.controls; }

  cargarVehiculos() {
    this.vehiculoService.consultarVehiculos().subscribe({
      next: (data) => {
        this.vehiculos.set(data.filter(v => v.activo));
        this.cargandoVehiculos.set(false);
      },
      error: () => {
        this.errorMessage.set('No se pudieron cargar los vehículos. Por favor recarga la página.');
        this.cargandoVehiculos.set(false);
      }
    });
  }

  obtenerUbicacion() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.latitud.set(position.coords.latitude);
          this.longitud.set(position.coords.longitude);
          if (!this.incidenteForm.get('direccion')?.value) {
            this.incidenteForm.patchValue({ direccion: 'Ubicación GPS Detectada' });
          }
        },
        (error) => {
          this.errorMessage.set('No se pudo obtener la ubicación GPS. Verifica los permisos de tu navegador.');
        }
      );
    } else {
      this.errorMessage.set('La geolocalización no es soportada por este navegador.');
    }
  }

  onSubmit() {
    if (this.incidenteForm.invalid) {
      this.incidenteForm.markAllAsTouched();
      return;
    }

    this.procesando.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const payload: IncidenteCreate = {
      ...this.incidenteForm.value,
      id_vehiculo: Number(this.incidenteForm.value.id_vehiculo),
      ubicacion_lat: this.latitud() !== null ? this.latitud() : undefined,
      ubicacion_lng: this.longitud() !== null ? this.longitud() : undefined
    };

    // Replace empty strings with undefined
    if (!payload.imagen_url) delete payload.imagen_url;
    if (!payload.audio_url) delete payload.audio_url;

    this.incidenteService.registrarIncidente(payload).subscribe({
      next: (res) => {
        this.successMessage.set('El incidente ha sido reportado y analizado por IA exitosamente.');
        this.procesando.set(false);
        setTimeout(() => {
          this.router.navigate(['/dashboard/incidentes/detalle', res.id_incidente]);
        }, 1500);
      },
      error: (err) => {
        this.procesando.set(false);
        this.errorMessage.set(err.error?.detail || 'Ocurrió un error al registrar el incidente inteligente.');
      }
    });
  }

  volver() {
    this.router.navigate(['/dashboard/incidentes']);
  }
}
