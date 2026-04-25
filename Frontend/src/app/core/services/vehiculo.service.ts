import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface Vehiculo {
  id_vehiculo: number;
  id_cliente: number;
  placa: string;
  marca: string;
  modelo: string;
  anio?: number;
  color?: string;
  tipo_vehiculo?: string;
  vin?: string;
  activo: boolean;
}

export interface VehiculoCreate {
  placa: string;
  marca: string;
  modelo: string;
  anio?: number;
  color?: string;
  tipo_vehiculo?: string;
  vin?: string;
}

export interface VehiculoUpdate {
  placa?: string;
  marca?: string;
  modelo?: string;
  anio?: number;
  color?: string;
  tipo_vehiculo?: string;
  vin?: string;
  activo?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class VehiculoService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/vehiculos`;

  consultarVehiculos(): Observable<Vehiculo[]> {
    return this.http.get<Vehiculo[]>(this.apiUrl);
  }

  obtenerVehiculo(id: number): Observable<Vehiculo> {
    return this.http.get<Vehiculo>(`${this.apiUrl}/${id}`);
  }

  registrarVehiculo(vehiculo: VehiculoCreate): Observable<Vehiculo> {
    return this.http.post<Vehiculo>(this.apiUrl, vehiculo);
  }

  actualizarVehiculo(id: number, vehiculo: VehiculoUpdate): Observable<Vehiculo> {
    return this.http.patch<Vehiculo>(`${this.apiUrl}/${id}`, vehiculo);
  }
}
