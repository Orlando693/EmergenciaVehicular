import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';

export interface LogEntry {
  id_bitacora: number;
  modulo: string;
  accion: string;
  ip: string;
  rol: string;
  created_at?: string;
  usuario_email?: string;
  id_usuario?: number;
}

export interface BitacoraPage {
  items: LogEntry[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class BitacoraService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/bitacora`;

  getLogs(skip = 0, limit = 20): Observable<BitacoraPage> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<BitacoraPage>(this.apiUrl, { params });
  }

  logAction(modulo: string, accion: string): Observable<any> {
    return this.http.post(this.apiUrl, { modulo, accion });
  }

  deleteAll(): Observable<{ message: string; deleted: number }> {
    return this.http.delete<{ message: string; deleted: number }>(this.apiUrl);
  }
}
