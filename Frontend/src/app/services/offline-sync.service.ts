import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, of, BehaviorSubject } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { AuthService } from '../core/services/auth.service';

export interface EmergenciaOffline {
  client_sync_id: string;
  incidente: any;
  estado_sync: 'PENDIENTE' | 'SINCRONIZANDO' | 'SINCRONIZADA' | 'ERROR';
  mensaje_error?: string;
  created_at_local: string;
}

@Injectable({
  providedIn: 'root'
})
export class OfflineSyncService {
  private apiUrl = `${environment.apiUrl}/sincronizacion-offline/sincronizar-emergencia-offline`;
  private getStatusUrl = `${environment.apiUrl}/sincronizacion-offline/sincronizaciones`;

  /** Clave de storage aislada por tenant para evitar mezcla de datos entre tenants */
  private get storageKey(): string {
    const tenantId = this.authService.idTenant;
    return tenantId ? `emergencias_offline_${tenantId}` : 'emergencias_offline_guest';
  }

  private emergenciasSubject = new BehaviorSubject<EmergenciaOffline[]>([]);
  public emergencias$ = this.emergenciasSubject.asObservable();

  public simulatorIsOnline = true;

  constructor(private http: HttpClient, private authService: AuthService) {
    this.emergenciasSubject.next(this.getLocalEmergencias());
    
    // Escuchar eventos de red reales (si aplica)
    window.addEventListener('online', () => this.handleNetworkChange(true));
    window.addEventListener('offline', () => this.handleNetworkChange(false));
    
    // Intentar sincronizar al iniciar si hay pendients
    if (navigator.onLine) {
      this.syncPending();
    }
  }

  setSimulatedNetworkStatus(isOnline: boolean) {
    this.simulatorIsOnline = isOnline;
    if (isOnline) {
      this.syncPending();
    }
  }

  get isOnline(): boolean {
    // Para simplificar la prueba combinamos el simulador y el real
    return navigator.onLine && this.simulatorIsOnline;
  }

  private handleNetworkChange(isOnline: boolean) {
    if (isOnline && this.simulatorIsOnline) {
      this.syncPending();
    }
  }

  getLocalEmergencias(): EmergenciaOffline[] {
    const data = localStorage.getItem(this.storageKey);
    return data ? JSON.parse(data) : [];
  }

  guardarEmergenciaLocal(incidenteParams: any): EmergenciaOffline {
    const clientSyncId = crypto.randomUUID();
    const nuevaEmergencia: EmergenciaOffline = {
      client_sync_id: clientSyncId,
      incidente: incidenteParams,
      estado_sync: 'PENDIENTE',
      created_at_local: new Date().toISOString()
    };

    const emergencias = this.getLocalEmergencias();
    emergencias.push(nuevaEmergencia);
    localStorage.setItem(this.storageKey, JSON.stringify(emergencias));
    this.emergenciasSubject.next(emergencias);

    if (this.isOnline) {
      this.syncSingle(nuevaEmergencia);
    }

    return nuevaEmergencia;
  }

  private actualizarEstadoLocal(clientSyncId: string, info: Partial<EmergenciaOffline>) {
    const emergencias = this.getLocalEmergencias();
    const index = emergencias.findIndex(e => e.client_sync_id === clientSyncId);
    if (index > -1) {
      emergencias[index] = { ...emergencias[index], ...info };
      localStorage.setItem(this.storageKey, JSON.stringify(emergencias));
      this.emergenciasSubject.next(emergencias);
    }
  }

  syncPending() {
    const emergencias = this.getLocalEmergencias().filter(e => e.estado_sync === 'PENDIENTE' || e.estado_sync === 'ERROR');
    emergencias.forEach(emer => {
      this.syncSingle(emer);
    });
  }

  private syncSingle(emergencia: EmergenciaOffline) {
    if (!this.isOnline) return;

    this.actualizarEstadoLocal(emergencia.client_sync_id, { estado_sync: 'SINCRONIZANDO' });

    const payload = {
      client_sync_id: emergencia.client_sync_id,
      emergencia: emergencia.incidente,
      created_at_local: emergencia.created_at_local
    };

    this.http.post<any>(this.apiUrl, payload).subscribe({
      next: (res) => {
        // Puede responder que ya estaba sincronizada o que la creo
        this.actualizarEstadoLocal(emergencia.client_sync_id, { 
          estado_sync: 'SINCRONIZADA', 
          incidente: res.incidente || emergencia.incidente,
          mensaje_error: undefined
        });
      },
      error: (err) => {
        this.actualizarEstadoLocal(emergencia.client_sync_id, { 
          estado_sync: 'ERROR', 
          mensaje_error: err.error?.detail || err.message 
        });
      }
    });
  }

  limpiarSincronizadas() {
    let emergencias = this.getLocalEmergencias();
    emergencias = emergencias.filter(e => e.estado_sync !== 'SINCRONIZADA');
    localStorage.setItem(this.storageKey, JSON.stringify(emergencias));
    this.emergenciasSubject.next(emergencias);
  }
}