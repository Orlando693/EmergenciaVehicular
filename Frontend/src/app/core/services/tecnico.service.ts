import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Tecnico, TecnicoCreate } from '../../models/tecnico.model';

@Injectable({ providedIn: 'root' })
export class TecnicoService {
  private readonly api = environment.apiUrl;

  constructor(private http: HttpClient) {}

  listar(idTaller: number) {
    return this.http.get<Tecnico[]>(`${this.api}/talleres/${idTaller}/tecnicos`);
  }

  crear(idTaller: number, data: TecnicoCreate) {
    return this.http.post<Tecnico>(`${this.api}/talleres/${idTaller}/tecnicos`, data);
  }

  actualizar(idTaller: number, idTecnico: number, data: Partial<TecnicoCreate>) {
    return this.http.put<Tecnico>(`${this.api}/talleres/${idTaller}/tecnicos/${idTecnico}`, data);
  }

  desactivar(idTaller: number, idTecnico: number) {
    return this.http.delete(`${this.api}/talleres/${idTaller}/tecnicos/${idTecnico}`);
  }
}
