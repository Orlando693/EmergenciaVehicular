import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { OfflineSyncService, EmergenciaOffline } from '../../../../services/offline-sync.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-sincronizacion-offline',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sincronizacion-offline.component.html',
  styleUrls: ['./sincronizacion-offline.component.css']
})
export class SincronizacionOfflineComponent implements OnInit {
  emergencias: EmergenciaOffline[] = [];
  
  // Variables del formulario para simular la nueva emergencia
  tipoIncidente = 'FALLA_MECANICA';
  descripcion = '';
  latitud: number | null = null;
  longitud: number | null = null;

  isOnlineUI = true;

  constructor(
    public offlineSyncService: OfflineSyncService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.isOnlineUI = this.offlineSyncService.simulatorIsOnline;
    this.offlineSyncService.emergencias$.subscribe(data => {
      this.emergencias = data;
    });
    
    // Simular ubicación actual si está disponibe
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(position => {
        this.latitud = position.coords.latitude;
        this.longitud = position.coords.longitude;
      });
    }
  }

  toggleNetworkSimulator(): void {
    this.isOnlineUI = !this.isOnlineUI;
    this.offlineSyncService.setSimulatedNetworkStatus(this.isOnlineUI);
  }

  registrarEmergencia(): void {
    if (!this.descripcion || !this.tipoIncidente) {
      alert('Por favor complete la descripción y el tipo de incidente.');
      return;
    }

    const incidenteParams = {
      tipo_incidente: this.tipoIncidente,
      descripcion: this.descripcion,
      latitud: this.latitud || -17.78, // valores default en caso que no haya geoloc
      longitud: this.longitud || -63.18,
      id_cliente: this.authService.idUsuario // vinculamos al ID del usuario actual
    };

    this.offlineSyncService.guardarEmergenciaLocal(incidenteParams);
    
    // Resetear form
    this.descripcion = '';
    this.tipoIncidente = 'FALLA_MECANICA';
  }

  forzarSincronizacion(): void {
    this.offlineSyncService.syncPending();
  }

  limpiarHistorial(): void {
    if (confirm('¿Está seguro de limpiar las emergencias ya sincronizadas?')) {
      this.offlineSyncService.limpiarSincronizadas();
    }
  }
}