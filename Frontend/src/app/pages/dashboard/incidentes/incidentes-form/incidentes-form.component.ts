import { Component, inject, OnInit, signal, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { VehiculoService, Vehiculo } from '../../../../core/services/vehiculo.service';
import { IncidenteService, IncidenteCreate, IncidenteOut } from '../../../../core/services/incidente.service';
import { BitacoraService } from '../../../../services/bitacora.service';
import * as L from 'leaflet';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-incidentes-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './incidentes-form.component.html',
  styleUrl: './incidentes-form.component.css'
})
export class IncidentesFormComponent implements OnInit, AfterViewInit, OnDestroy {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private vehiculoService = inject(VehiculoService);
  private incidenteService = inject(IncidenteService);
  private bitacoraService = inject(BitacoraService);

  incidenteForm!: FormGroup;
  vehiculos = signal<Vehiculo[]>([]);

  cargandoVehiculos = signal(true);
  procesando = signal(false);

  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);

  latitud = signal<number | null>(null);
  longitud = signal<number | null>(null);

  // Archivos seleccionados
  imagenFile: File | null = null;
  audioFile: File | null = null;
  imagenPreviewUrl = signal<string | null>(null);
  audioPreviewUrl = signal<string | null>(null);
  imagenNombre = signal<string | null>(null);
  audioNombre = signal<string | null>(null);

  // Resultado IA tras envio
  resultadoIA = signal<IncidenteOut | null>(null);
  mostrarResultado = signal(false);

  // Mapa
  private map: L.Map | undefined;
  private marker: L.Marker | undefined;

  ngOnInit() {
    this.initForm();
    this.cargarVehiculos();

    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
    });
  }

  ngAfterViewInit() {
    setTimeout(() => this.initMap(), 150);
  }

  ngOnDestroy() {
    if (this.map) {
      this.map.remove();
    }
    const preview = this.imagenPreviewUrl();
    if (preview) URL.revokeObjectURL(preview);
    const audioPreview = this.audioPreviewUrl();
    if (audioPreview) URL.revokeObjectURL(audioPreview);
  }

  initForm() {
    this.incidenteForm = this.fb.group({
      id_vehiculo: ['', Validators.required],
      descripcion: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(1000)]],
      direccion: ['']
    });
  }

  get f() { return this.incidenteForm.controls; }

  private initMap() {
    if (this.map) return;
    this.map = L.map('incident-map').setView([4.6097, -74.0817], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.map.on('click', (e: L.LeafletMouseEvent) => {
      this.setMapMarker(e.latlng.lat, e.latlng.lng);
      this.reverseGeocode(e.latlng.lat, e.latlng.lng);
    });
  }

  private setMapMarker(lat: number, lng: number) {
    if (!this.map) return;
    this.latitud.set(lat);
    this.longitud.set(lng);

    if (this.marker) {
      this.marker.setLatLng([lat, lng]);
    } else {
      this.marker = L.marker([lat, lng], {
        title: 'Ubicacion del incidente'
      }).addTo(this.map);
    }

    this.marker.bindPopup(
      `<b>Incidente aqui</b><br>Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`
    ).openPopup();
  }

  private async reverseGeocode(lat: number, lng: number) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&accept-language=es`;
      const res = await fetch(url);
      const data = await res.json();
      const direccion = data.display_name ?? `Coordenadas: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
      this.incidenteForm.patchValue({ direccion });
    } catch {
      this.incidenteForm.patchValue({ direccion: `Coordenadas: ${lat.toFixed(5)}, ${lng.toFixed(5)}` });
    }
  }

  cargarVehiculos() {
    this.vehiculoService.consultarVehiculos().subscribe({
      next: (data) => {
        this.vehiculos.set(data.filter(v => v.activo));
        this.cargandoVehiculos.set(false);
      },
      error: () => {
        this.errorMessage.set('No se pudieron cargar los vehiculos. Por favor recarga la pagina.');
        this.cargandoVehiculos.set(false);
      }
    });
  }

  obtenerUbicacion() {
    if (!navigator.geolocation) {
      this.errorMessage.set('La geolocalizacion no es soportada por este navegador.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        this.setMapMarker(lat, lng);
        this.reverseGeocode(lat, lng);
        this.map?.setView([lat, lng], 17);
      },
      () => {
        this.errorMessage.set('No se pudo obtener la ubicacion GPS. Verifica los permisos del navegador o selecciona en el mapa.');
      }
    );
  }

  onImageChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (file) {
      this.imagenFile = file;
      this.imagenNombre.set(file.name);
      const prev = this.imagenPreviewUrl();
      if (prev) URL.revokeObjectURL(prev);
      this.imagenPreviewUrl.set(URL.createObjectURL(file));
    }
  }

  onAudioChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (file) {
      this.audioFile = file;
      this.audioNombre.set(file.name);
      const prev = this.audioPreviewUrl();
      if (prev) URL.revokeObjectURL(prev);
      this.audioPreviewUrl.set(URL.createObjectURL(file));
    }
  }

  limpiarImagen() {
    this.imagenFile = null;
    this.imagenNombre.set(null);
    const prev = this.imagenPreviewUrl();
    if (prev) URL.revokeObjectURL(prev);
    this.imagenPreviewUrl.set(null);
  }

  limpiarAudio() {
    this.audioFile = null;
    this.audioNombre.set(null);
    const prev = this.audioPreviewUrl();
    if (prev) URL.revokeObjectURL(prev);
    this.audioPreviewUrl.set(null);
  }

  irAlDetalle() {
    const res = this.resultadoIA();
    if (res) {
      this.router.navigate(['/dashboard/incidentes/detalle', res.id_incidente]);
    }
  }

  async onSubmit() {
    this.errorMessage.set(null);

    if (this.incidenteForm.invalid) {
      this.incidenteForm.markAllAsTouched();
      return;
    }

    if (!this.latitud() || !this.longitud()) {
      // By default use coordinates 0,0 if map has failed loading to let the user pass
      this.latitud.set(0);
      this.longitud.set(0);
    }

    this.procesando.set(true);
    this.mostrarResultado.set(false);

    try {
      let imagenUrlV: string | undefined;
      let audioUrlV: string | undefined;

      if (this.imagenFile) {
        const resImg = await firstValueFrom(this.incidenteService.uploadEvidence(this.imagenFile));
        imagenUrlV = resImg.url;
      }

      if (this.audioFile) {
        const resAud = await firstValueFrom(this.incidenteService.uploadEvidence(this.audioFile));
        audioUrlV = resAud.url;
      }

      const payload: IncidenteCreate = {
        ...this.incidenteForm.value,
        id_vehiculo: Number(this.incidenteForm.value.id_vehiculo),
        ubicacion_lat: this.latitud()!,
        ubicacion_lng: this.longitud()!,
        imagen_url: imagenUrlV,
        audio_url: audioUrlV
      };

      const res = await firstValueFrom(this.incidenteService.registrarIncidente(payload));

      this.bitacoraService.logAction('Incidentes', `Incidente registrado #${res.id_incidente} — Clasificación IA: ${res.clasificacion_ia ?? 'Pendiente'}`).subscribe();

      this.resultadoIA.set(res);
      this.mostrarResultado.set(true);
      this.successMessage.set('Incidente registrado y analizado por IA exitosamente.');
      this.procesando.set(false);

    } catch (err: any) {
      this.procesando.set(false);
      this.errorMessage.set(err.error?.detail ?? 'Ocurrio un error al registrar el incidente o subir archivos.');
    }
  }

  volver() {
    this.router.navigate(['/dashboard/incidentes']);
  }
}
