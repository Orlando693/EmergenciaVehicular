import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

interface TenantInfo  { id_tenant: number; nombre: string; slug: string; estado: string; created_at: string; }
interface Metricas     { total_usuarios: number; total_talleres: number; total_clientes: number; total_incidentes: number; total_pagos: number; ingresos_total: number; incidentes_activos: number; }
interface UsuarioRow  { id_usuario: number; nombres: string; apellidos: string; email: string; telefono: string | null; estado: string; roles: string[]; created_at: string; }
interface TallerRow   { id_taller: number; nombre_comercial: string; estado: string; telefono: string | null; email: string | null; direccion: string | null; created_at: string; }
interface Aislamiento { tenants_detectados: number; aislado: boolean; mensaje: string; }

interface AdminData {
  tenant:      TenantInfo;
  metricas:    Metricas;
  usuarios:    UsuarioRow[];
  talleres:    TallerRow[];
  aislamiento: Aislamiento;
}

type Tab = 'overview' | 'usuarios' | 'talleres' | 'aislamiento';

@Component({
  selector: 'app-multi-tenant-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyPipe],
  templateUrl: './multi-tenant-admin.component.html',
  styleUrls: ['./multi-tenant-admin.component.css'],
})
export class MultiTenantAdminComponent implements OnInit {
  private api = `${environment.apiUrl}/multi-tenant-admin`;

  data    = signal<AdminData | null>(null);
  loading = signal(true);
  error   = signal('');
  saving  = signal(false);
  flash   = signal('');

  tab = signal<Tab>('overview');

  editNombre = '';
  showEdit   = false;

  usuarioBusq = '';
  tallerBusq  = '';

  constructor(private http: HttpClient, public auth: AuthService) {}

  ngOnInit() { this.cargar(); }

  private get headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  cargar() {
    this.loading.set(true);
    this.error.set('');
    this.http.get<AdminData>(this.api, { headers: this.headers }).subscribe({
      next: d => { this.data.set(d); this.editNombre = d.tenant.nombre; this.loading.set(false); },
      error: e => { this.error.set(e?.error?.detail ?? 'Error al cargar'); this.loading.set(false); },
    });
  }

  abrirEdit() { const d = this.data(); if (d) { this.editNombre = d.tenant.nombre; this.showEdit = true; } }
  cerrarEdit() { this.showEdit = false; }

  guardarNombre() {
    if (!this.editNombre.trim()) return;
    this.saving.set(true);
    this.http.put<TenantInfo>(`${this.api}/tenant`, { nombre: this.editNombre }, { headers: this.headers }).subscribe({
      next: t => {
        const d = this.data();
        if (d) this.data.set({ ...d, tenant: t });
        this.saving.set(false);
        this.showEdit = false;
        this.mostrarFlash('Nombre del tenant actualizado correctamente.');
      },
      error: e => { this.error.set(e?.error?.detail ?? 'Error al guardar'); this.saving.set(false); },
    });
  }

  private mostrarFlash(msg: string) {
    this.flash.set(msg);
    setTimeout(() => this.flash.set(''), 3500);
  }

  get usuariosFiltrados(): UsuarioRow[] {
    const d = this.data();
    if (!d) return [];
    const q = this.usuarioBusq.toLowerCase();
    return q ? d.usuarios.filter(u => `${u.nombres} ${u.apellidos} ${u.email}`.toLowerCase().includes(q)) : d.usuarios;
  }

  get talleresFiltrados(): TallerRow[] {
    const d = this.data();
    if (!d) return [];
    const q = this.tallerBusq.toLowerCase();
    return q ? d.talleres.filter(t => t.nombre_comercial.toLowerCase().includes(q)) : d.talleres;
  }

  estadoClass(e: string): string {
    return { ACTIVO: 'badge-green', INACTIVO: 'badge-red', SUSPENDIDO: 'badge-orange' }[e] ?? 'badge-gray';
  }

  rolColor(r: string): string {
    return { ADMINISTRADOR: '#6366f1', TALLER: '#f59e0b', CLIENTE: '#10b981', TECNICO: '#3b82f6' }[r] ?? '#94a3b8';
  }

  trackId(_: number, u: { id_usuario?: number; id_taller?: number }) { return u.id_usuario ?? u.id_taller; }
}
