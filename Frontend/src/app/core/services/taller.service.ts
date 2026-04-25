import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Taller, TallerCreate } from '../../models/taller.model';
import { IncidenteOut } from './incidente.service';

@Injectable({ providedIn: 'root' })
export class TallerService {
  private readonly api = `${environment.apiUrl}/talleres`;

  constructor(private http: HttpClient) {}

  solicitudesDisponibles() {
    return this.http.get<IncidenteOut[]>(`${this.api}/solicitudes-disponibles`);
  }

  detalleSolicitudDisponible(id: number) {
    return this.http.get<IncidenteOut>(`${this.api}/solicitudes-disponibles/${id}`);
  }

  registrar(data: TallerCreate) {
    return this.http.post<Taller>(this.api, data);
  }

  listar(estado?: string) {
    const params = estado ? `?estado=${estado}` : '';
    return this.http.get<Taller[]>(`${this.api}${params}`);
  }

  obtener(id: number) {
    return this.http.get<Taller>(`${this.api}/${id}`);
  }

  miTaller() {
    return this.http.get<Taller>(`${this.api}/mi-taller`);
  }

  actualizar(data: Partial<TallerCreate>) {
    return this.http.put<Taller>(`${this.api}/mi-taller`, data);
  }

  actualizarTallerAdmin(id: number, data: Partial<TallerCreate>) {
    return this.http.put<Taller>(`${this.api}/${id}`, data);
  }

  cambiarEstado(id: number, estado: string) {
    return this.http.patch<Taller>(`${this.api}/${id}/estado`, { estado_registro: estado });
  }
}
