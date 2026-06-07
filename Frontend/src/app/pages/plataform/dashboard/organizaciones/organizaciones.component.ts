import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  PlatformService,
  TenantPlatform,
  PlanPlatform,
  PlanCreate,
} from '../../../../services/platform.service';

interface NuevaTenantForm {
  nombre: string;
  slug:   string;
  id_plan?: number;
}

interface EditPlanForm {
  slug:                       string;
  nombre:                     string;
  descripcion:                string;
  precio:                     number;
  max_incidentes_mes:         number;
  max_tecnicos:               number;
  max_usuarios:               number;
  tiene_ia:                   boolean;
  tiene_reportes_avanzados:   boolean;
  tiene_soporte_prioritario:  boolean;
  tiene_notificaciones_push:  boolean;
  orden:                      number;
}

@Component({
  selector: 'app-organizaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './organizaciones.component.html',
  styleUrls: ['./organizaciones.component.css'],
})
export class OrganizacionesComponent implements OnInit {
  tenants  = signal<TenantPlatform[]>([]);
  planes   = signal<PlanPlatform[]>([]);
  loading  = signal(false);
  error    = signal('');
  msg      = signal('');

  // ── Modales ──────────────────────────────────────────────────────────────
  showNuevoTenant = signal(false);
  showNuevoPlan   = signal(false);
  showEditPlan    = signal(false);
  showAsignarPlan = signal(false);

  selectedTenant = signal<TenantPlatform | null>(null);
  selectedPlan   = signal<PlanPlatform | null>(null);

  nuevoTenantForm: NuevaTenantForm = { nombre: '', slug: '', id_plan: undefined };

  editPlanForm: EditPlanForm = {
    slug: '', nombre: '', descripcion: '', precio: 0,
    max_incidentes_mes: 0, max_tecnicos: 0, max_usuarios: 0,
    tiene_ia: false, tiene_reportes_avanzados: false,
    tiene_soporte_prioritario: false, tiene_notificaciones_push: true,
    orden: 99,
  };

  asignarPlanId: number | undefined;

  constructor(private svc: PlatformService) {}

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.loading.set(true);
    this.svc.getTenants().subscribe({
      next: t => this.tenants.set(t),
      error: () => this.error.set('Error al cargar organizaciones'),
    });
    this.svc.getPlanes().subscribe({
      next: p => { this.planes.set(p); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar planes'); this.loading.set(false); },
    });
  }

  // ── Tenants ──────────────────────────────────────────────────────────────

  abrirNuevoTenant() {
    this.nuevoTenantForm = { nombre: '', slug: '', id_plan: this.planes()[0]?.id_plan };
    this.showNuevoTenant.set(true);
  }

  crearTenant() {
    if (!this.nuevoTenantForm.nombre || !this.nuevoTenantForm.slug) return;
    this.svc.crearTenant(this.nuevoTenantForm).subscribe({
      next: t => {
        this.tenants.update(arr => [t, ...arr]);
        this.showNuevoTenant.set(false);
        this.flash('Organización creada correctamente');
      },
      error: e => this.error.set(e?.error?.detail ?? 'Error al crear organización'),
    });
  }

  activar(t: TenantPlatform) {
    this.svc.cambiarEstadoTenant(t.id_tenant, 'ACTIVO').subscribe({
      next: u => this.updateTenant(u),
      error: () => this.error.set('Error al activar organización'),
    });
  }

  suspender(t: TenantPlatform) {
    this.svc.cambiarEstadoTenant(t.id_tenant, 'SUSPENDIDO').subscribe({
      next: u => this.updateTenant(u),
      error: () => this.error.set('Error al suspender organización'),
    });
  }

  abrirAsignarPlan(t: TenantPlatform) {
    this.selectedTenant.set(t);
    this.asignarPlanId = this.planes().find(p => p.nombre === t.plan_nombre)?.id_plan;
    this.showAsignarPlan.set(true);
  }

  guardarPlanTenant() {
    const t = this.selectedTenant();
    if (!t || !this.asignarPlanId) return;
    this.svc.asignarPlan(t.id_tenant, this.asignarPlanId).subscribe({
      next: () => { this.cargar(); this.showAsignarPlan.set(false); this.flash('Plan asignado'); },
      error: () => this.error.set('Error al asignar plan'),
    });
  }

  // ── Planes ────────────────────────────────────────────────────────────────

  abrirNuevoPlan() {
    this.editPlanForm = {
      slug: '', nombre: '', descripcion: '', precio: 0,
      max_incidentes_mes: 0, max_tecnicos: 0, max_usuarios: 0,
      tiene_ia: false, tiene_reportes_avanzados: false,
      tiene_soporte_prioritario: false, tiene_notificaciones_push: true,
      orden: 99,
    };
    this.selectedPlan.set(null);
    this.showNuevoPlan.set(true);
  }

  abrirEditarPlan(p: PlanPlatform) {
    this.selectedPlan.set(p);
    this.editPlanForm = { ...p, descripcion: p.descripcion ?? '' };
    this.showEditPlan.set(true);
  }

  guardarPlan() {
    const payload: PlanCreate = { ...this.editPlanForm };
    this.svc.crearPlan(payload).subscribe({
      next: p => {
        this.planes.update(arr => [...arr, p]);
        this.showNuevoPlan.set(false);
        this.flash('Plan creado');
      },
      error: e => this.error.set(e?.error?.detail ?? 'Error al crear plan'),
    });
  }

  actualizarPlan() {
    const p = this.selectedPlan();
    if (!p) return;
    const payload: PlanCreate = { ...this.editPlanForm };
    this.svc.editarPlan(p.id_plan, payload).subscribe({
      next: u => {
        this.planes.update(arr => arr.map(x => x.id_plan === u.id_plan ? u : x));
        this.showEditPlan.set(false);
        this.flash('Plan actualizado');
      },
      error: e => this.error.set(e?.error?.detail ?? 'Error al actualizar plan'),
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  private updateTenant(updated: TenantPlatform) {
    this.tenants.update(arr => arr.map(t => t.id_tenant === updated.id_tenant ? updated : t));
  }

  private flash(msg: string) {
    this.msg.set(msg);
    setTimeout(() => this.msg.set(''), 3000);
  }

  formatLimites(p: PlanPlatform): string {
    return `U${p.max_usuarios} · P${p.max_tecnicos} · C${p.max_incidentes_mes}`;
  }

  formatFeatures(p: PlanPlatform): string {
    const parts: string[] = [];
    parts.push(`CRM:${p.tiene_ia ? 'sí' : 'no'}`);
    parts.push(`Notif:${p.tiene_notificaciones_push ? 'sí' : 'no'}`);
    parts.push(`Reportes:${p.tiene_reportes_avanzados ? 'sí' : 'no'}`);
    return parts.join(' · ');
  }
}
