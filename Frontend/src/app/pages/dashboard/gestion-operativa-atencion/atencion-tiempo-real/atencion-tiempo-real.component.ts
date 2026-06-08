import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import * as L from 'leaflet';

import {
  AtencionSeguimientoOut,
  AtencionTiempoRealService,
  UbicacionTecnico,
} from '../../../../services/atencion-tiempo-real.service';
import { AuthService } from '../../../../core/services/auth.service';
import { IncidenteOut, IncidenteService } from '../../../../core/services/incidente.service';

@Component({
  selector: 'app-atencion-tiempo-real',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './atencion-tiempo-real.component.html',
  styleUrls: ['./atencion-tiempo-real.component.css'],
})
export class AtencionTiempoRealComponent implements OnInit, OnDestroy {
  idIncidente: number | null = null;
  seguimiento: AtencionSeguimientoOut | null = null;
  incidentes: IncidenteOut[] = [];

  loading = true;
  loadingList = true;
  error = '';
  nuevoEstado = '';
  observacion = '';
  esTaller = false;
  esCliente = false;
  compartiendo = false;
  gpsError = '';
  ultimaUbicacionEnviada: UbicacionTecnico | null = null;

  estadosPermitidos = ['EN_PROCESO', 'RESUELTO', 'CANCELADO'];

  private wsSubscription?: Subscription;
  private routeSubscription?: Subscription;
  private watchId: number | null = null;
  private map?: L.Map;
  private clienteMarker?: L.Marker;
  private tecnicoMarker?: L.Marker;
  private routeLine?: L.Polyline;

  private readonly fallbackCenter: L.LatLngExpression = [-17.7833, -63.1821];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private atencionService: AtencionTiempoRealService,
    private incidenteService: IncidenteService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    const rol = this.authService.rol.toUpperCase();
    this.esTaller = rol === 'TALLER';
    this.esCliente = rol === 'CLIENTE';

    this.cargarIncidentes();

    this.routeSubscription = this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      this.idIncidente = id ? Number(id) : null;
      if (this.idIncidente) {
        this.cargarSeguimiento(this.idIncidente);
        this.conectarWs(this.idIncidente);
      } else {
        this.loading = false;
        this.seguimiento = null;
        this.desconectarWs();
        this.destroyMap();
      }
    });

    this.wsSubscription = this.atencionService.eventos$.subscribe(evento => {
      if (evento.tipo === 'SEGUIMIENTO_INICIAL') {
        this.seguimiento = evento.data;
        this.renderMapSoon();
      } else if (evento.tipo === 'UBICACION_TECNICO') {
        this.aplicarUbicacionTecnico(evento.data);
      } else if (evento.tipo) {
        if (this.idIncidente) this.cargarSeguimiento(this.idIncidente, false);
      }
    });
  }

  cargarIncidentes(): void {
    this.loadingList = true;
    this.incidenteService.consultarHistorial().subscribe({
      next: data => {
        const activos = new Set(['ASIGNADO', 'EN_PROCESO', 'REPORTADO', 'RESUELTO']);
        this.incidentes = data.filter(i => activos.has(i.estado) && (i.id_taller || this.esTaller));
        this.loadingList = false;
      },
      error: () => {
        this.loadingList = false;
      },
    });
  }

  seleccionarIncidente(id: number): void {
    this.router.navigate(['/dashboard/atencion-tiempo-real', id]);
  }

  cargarSeguimiento(id: number, showLoading = true): void {
    if (showLoading) {
      this.loading = true;
      this.error = '';
    }

    this.atencionService.obtenerSeguimiento(id).subscribe({
      next: data => {
        this.seguimiento = data;
        this.loading = false;
        this.renderMapSoon();
      },
      error: err => {
        this.error = err?.error?.detail || 'No se pudo cargar el seguimiento en tiempo real.';
        this.loading = false;
      },
    });
  }

  aceptar(): void {
    if (!this.idIncidente) return;
    this.atencionService.aceptarAtencion(this.idIncidente, this.observacion).subscribe({
      next: () => {
        this.observacion = '';
        this.cargarSeguimiento(this.idIncidente!);
      },
      error: err => alert('Error al aceptar la atención: ' + (err.error?.detail || err.message)),
    });
  }

  rechazar(): void {
    if (!this.idIncidente) return;
    this.atencionService.rechazarAtencion(this.idIncidente, this.observacion).subscribe({
      next: () => {
        this.observacion = '';
        this.detenerTracking();
        this.router.navigate(['/dashboard/atencion-tiempo-real']);
      },
      error: err => alert('Error al rechazar la atención: ' + (err.error?.detail || err.message)),
    });
  }

  actualizarEstado(): void {
    if (!this.idIncidente || !this.nuevoEstado) return;
    this.atencionService.actualizarEstado(this.idIncidente, this.nuevoEstado, this.observacion).subscribe({
      next: () => {
        this.nuevoEstado = '';
        this.observacion = '';
        this.cargarSeguimiento(this.idIncidente!);
      },
      error: err => alert('Error al actualizar el estado: ' + (err.error?.detail || err.message)),
    });
  }

  iniciarTracking(): void {
    if (!this.idIncidente) return;
    if (!navigator.geolocation) {
      this.gpsError = 'Este navegador no soporta geolocalización.';
      return;
    }

    this.gpsError = '';
    this.compartiendo = true;
    this.watchId = navigator.geolocation.watchPosition(
      pos => this.enviarPosicion(pos),
      err => {
        this.gpsError = err.message || 'No se pudo obtener ubicación GPS.';
        this.compartiendo = false;
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 },
    );
  }

  detenerTracking(): void {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
    this.compartiendo = false;
  }

  private enviarPosicion(pos: GeolocationPosition): void {
    if (!this.idIncidente) return;
    this.atencionService.enviarUbicacion(this.idIncidente, {
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      precision: pos.coords.accuracy,
      velocidad: pos.coords.speed,
      rumbo: pos.coords.heading,
    }).subscribe({
      next: ubicacion => {
        this.ultimaUbicacionEnviada = ubicacion;
        this.aplicarUbicacionTecnico(ubicacion);
      },
      error: err => {
        this.gpsError = err?.error?.detail || 'No se pudo enviar la ubicación.';
      },
    });
  }

  private conectarWs(id: number): void {
    const token = this.authService.getToken();
    if (token) this.atencionService.conectarWebSocket(id, token);
  }

  private desconectarWs(): void {
    this.atencionService.desconectarWebSocket();
  }

  private aplicarUbicacionTecnico(ubicacion: UbicacionTecnico): void {
    if (!this.seguimiento) return;
    this.seguimiento = { ...this.seguimiento, ubicacion_tecnico: ubicacion };
    this.renderMapSoon();
  }

  private renderMapSoon(): void {
    setTimeout(() => this.renderMap(), 0);
  }

  private renderMap(): void {
    if (!this.seguimiento || typeof window === 'undefined') return;

    const cliente = this.clienteLatLng();
    const tecnico = this.tecnicoLatLng();
    const center = tecnico || cliente || this.fallbackCenter;

    if (!this.map) {
      const el = document.getElementById('tracking-map');
      if (!el) return;
      this.map = L.map(el, { zoomControl: true }).setView(center, 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap',
      }).addTo(this.map);
    }

    this.map.invalidateSize();

    if (cliente) {
      if (!this.clienteMarker) {
        this.clienteMarker = L.marker(cliente, { icon: this.markerIcon('cliente') }).addTo(this.map);
      } else {
        this.clienteMarker.setLatLng(cliente);
      }
      this.clienteMarker.bindPopup('Cliente / vehículo dañado');
    }

    if (tecnico) {
      if (!this.tecnicoMarker) {
        this.tecnicoMarker = L.marker(tecnico, { icon: this.markerIcon('tecnico') }).addTo(this.map);
      } else {
        this.tecnicoMarker.setLatLng(tecnico);
      }
      this.tecnicoMarker.bindPopup('Técnico en camino');
    }

    if (cliente && tecnico) {
      const points = [cliente, tecnico] as L.LatLngExpression[];
      if (!this.routeLine) {
        this.routeLine = L.polyline(points, { color: '#2563eb', weight: 4, dashArray: '8 8' }).addTo(this.map);
      } else {
        this.routeLine.setLatLngs(points);
      }
      this.map.fitBounds(L.latLngBounds(points).pad(0.25));
    } else {
      this.map.setView(center, 14);
    }
  }

  private clienteLatLng(): L.LatLngExpression | null {
    const inc = this.seguimiento?.incidente;
    const lat = Number(inc?.ubicacion_lat ?? 0);
    const lng = Number(inc?.ubicacion_lng ?? 0);
    if (!lat || !lng) return null;
    return [lat, lng];
  }

  private tecnicoLatLng(): L.LatLngExpression | null {
    const u = this.seguimiento?.ubicacion_tecnico;
    if (u?.lat && u?.lng) return [u.lat, u.lng];

    const taller = this.seguimiento?.taller;
    const lat = Number(taller?.latitud ?? 0);
    const lng = Number(taller?.longitud ?? 0);
    if (!lat || !lng) return null;
    return [lat, lng];
  }

  private markerIcon(type: 'cliente' | 'tecnico'): L.DivIcon {
    const label = type === 'cliente' ? '🚗' : '🔧';
    const color = type === 'cliente' ? '#ef4444' : '#2563eb';
    return L.divIcon({
      className: 'tracking-div-icon',
      html: `<div style="background:${color};">${label}</div>`,
      iconSize: [38, 38],
      iconAnchor: [19, 19],
    });
  }

  distanciaKm(): number | null {
    const c = this.clienteLatLng() as [number, number] | null;
    const t = this.tecnicoLatLng() as [number, number] | null;
    if (!c || !t) return null;
    const toRad = (v: number) => v * Math.PI / 180;
    const r = 6371;
    const dLat = toRad(t[0] - c[0]);
    const dLng = toRad(t[1] - c[1]);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(c[0])) * Math.cos(toRad(t[0])) * Math.sin(dLng / 2) ** 2;
    return r * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  etaMin(): number | null {
    const d = this.distanciaKm();
    if (d == null) return null;
    const velocidadKmh = Math.max(15, Number(this.seguimiento?.ubicacion_tecnico?.velocidad ?? 0) * 3.6 || 30);
    return Math.max(1, Math.round((d / velocidadKmh) * 60));
  }

  badgeClase(estado: string): string {
    const map: Record<string, string> = {
      REPORTADO: 'bg-yellow-100 text-yellow-700',
      ASIGNADO: 'bg-amber-100 text-amber-700',
      EN_PROCESO: 'bg-blue-100 text-blue-700',
      RESUELTO: 'bg-emerald-100 text-emerald-700',
      PAGADO: 'bg-teal-100 text-teal-700',
      CANCELADO: 'bg-red-100 text-red-700',
    };
    return map[estado] ?? 'bg-slate-100 text-slate-700';
  }

  private destroyMap(): void {
    if (this.map) {
      this.map.remove();
      this.map = undefined;
      this.clienteMarker = undefined;
      this.tecnicoMarker = undefined;
      this.routeLine = undefined;
    }
  }

  ngOnDestroy(): void {
    this.detenerTracking();
    this.wsSubscription?.unsubscribe();
    this.routeSubscription?.unsubscribe();
    this.desconectarWs();
    this.destroyMap();
  }
}
