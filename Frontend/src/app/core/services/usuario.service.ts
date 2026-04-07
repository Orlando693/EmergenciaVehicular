import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Usuario, UsuarioCreate, UsuarioUpdate } from '../../models/usuario.model';

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private readonly api = `${environment.apiUrl}/usuarios`;

  constructor(private http: HttpClient) {}

  registrar(data: UsuarioCreate) {
    return this.http.post<Usuario>(this.api, data);
  }

  listar() {
    return this.http.get<Usuario[]>(this.api);
  }

  obtener(id: number) {
    return this.http.get<Usuario>(`${this.api}/${id}`);
  }

  miPerfil() {
    return this.http.get<Usuario>(`${this.api}/me`);
  }

  actualizarPerfil(data: UsuarioUpdate) {
    return this.http.put<Usuario>(`${this.api}/me`, data);
  }

  cambiarEstado(id: number, estado: string) {
    return this.http.patch<Usuario>(`${this.api}/${id}/estado`, { estado });
  }
}
