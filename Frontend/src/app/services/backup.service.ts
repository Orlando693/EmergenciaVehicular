import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

export interface BackupRegistro {
  id_backup:      number;
  id_tenant:      number;
  id_usuario:     number | null;
  tipo:           'MANUAL' | 'AUTOMATICO';
  estado:         'COMPLETADO' | 'FALLIDO';
  nombre_archivo: string | null;
  tamano_bytes:   number;
  created_at:     string;
}

export interface BackupConfig {
  id_config:      number;
  id_tenant:      number;
  activo:         boolean;
  frecuencia:     'DIARIO' | 'SEMANAL' | 'MENSUAL';
  hora:           string;
  proximo_backup: string | null;
  ultimo_backup:  string | null;
  updated_at:     string;
}

export interface BackupConfigUpdate {
  activo:    boolean;
  frecuencia: string;
  hora:      string;
}

@Injectable({ providedIn: 'root' })
export class BackupService {
  private readonly api = `${environment.apiUrl}/backup`;

  constructor(private http: HttpClient) {}

  generarManual() {
    return this.http.post<BackupRegistro>(this.api, {});
  }

  listar() {
    return this.http.get<BackupRegistro[]>(this.api);
  }

  eliminar(id: number) {
    return this.http.delete(`${this.api}/${id}`);
  }

  descargarUrl(id: number): string {
    return `${this.api}/${id}/descargar`;
  }

  obtenerConfig() {
    return this.http.get<BackupConfig>(`${this.api}/config`);
  }

  actualizarConfig(data: BackupConfigUpdate) {
    return this.http.put<BackupConfig>(`${this.api}/config`, data);
  }

  checkAuto() {
    return this.http.post<{ ejecutado: boolean; id_backup?: number; nombre?: string }>(
      `${this.api}/check-auto`, {}
    );
  }
}
