import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

interface Permiso { id_permiso: number; codigo: string; descripcion: string; }
interface Rol     { id_rol: number; nombre: string; descripcion: string; activo: boolean; permisos: Permiso[]; }

@Component({
  selector: 'app-roles',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './roles.component.html',
  styleUrl: './roles.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class RolesComponent implements OnInit {
  roles        = signal<Rol[]>([]);
  permisos     = signal<Permiso[]>([]);
  loading      = signal(true);
  showForm     = signal(false);
  success      = signal('');
  error        = signal('');
  saving       = signal(false);

  rolEditando    = signal<Rol | null>(null);
  permisosMarcados = signal<Set<number>>(new Set());
  savingEdit     = signal(false);
  deletingId     = signal<number | null>(null);

  form:     FormGroup;
  editForm: FormGroup;
  private api = `${environment.apiUrl}/roles`;

  constructor(private http: HttpClient, private fb: FormBuilder) {
    this.form = this.fb.group({
      nombre:      ['', Validators.required],
      descripcion: [''],
    });
    this.editForm = this.fb.group({
      nombre:      ['', Validators.required],
      descripcion: [''],
      activo:      [true],
    });
  }

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    this.http.get<Rol[]>(this.api).subscribe({
      next:  (r) => { this.roles.set(r); this.loading.set(false); },
      error: ()  => { this.error.set('Error al cargar roles'); this.loading.set(false); },
    });
    this.http.get<Permiso[]>(`${this.api}/permisos`).subscribe({
      next: (p) => this.permisos.set(p),
    });
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    this.error.set('');
    this.http.post<Rol>(this.api, this.form.value).subscribe({
      next: (r) => {
        this.success.set('Rol creado'); this.showForm.set(false);
        this.form.reset(); this.roles.update(list => [...list, r]); this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error al crear rol'); this.saving.set(false); },
    });
  }

  abrirEdicion(rol: Rol) {
    this.rolEditando.set(rol);
    this.editForm.patchValue({
      nombre:      rol.nombre,
      descripcion: rol.descripcion ?? '',
      activo:      rol.activo,
    });
    this.permisosMarcados.set(new Set(rol.permisos.map(p => p.id_permiso)));
    this.error.set('');
  }

  cerrarEdicion() {
    this.rolEditando.set(null);
    this.error.set('');
  }

  togglePermiso(id: number) {
    this.permisosMarcados.update(set => {
      const next = new Set(set);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  tienePermiso(id: number): boolean {
    return this.permisosMarcados().has(id);
  }

  guardarEdicion() {
    if (this.editForm.invalid) { this.editForm.markAllAsTouched(); return; }
    const rol = this.rolEditando();
    if (!rol) return;
    this.savingEdit.set(true);
    this.error.set('');
    const id = rol.id_rol;

    this.http.put<Rol>(`${this.api}/${id}`, this.editForm.value).subscribe({
      next: () => {
        const ids = Array.from(this.permisosMarcados());
        this.http.put<Rol>(`${this.api}/${id}/permisos`, { id_permisos: ids }).subscribe({
          next: (updated) => {
            this.roles.update(list => list.map(r => r.id_rol === id ? updated : r));
            this.success.set('Rol actualizado correctamente');
            this.rolEditando.set(null);
            this.savingEdit.set(false);
            setTimeout(() => this.success.set(''), 3000);
          },
          error: (e) => { this.error.set(e.error?.detail ?? 'Error al asignar permisos'); this.savingEdit.set(false); },
        });
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error al actualizar rol'); this.savingEdit.set(false); },
    });
  }

  eliminarRol(rol: Rol) {
    if (!confirm(`¿Eliminar el rol "${rol.nombre}"? Esta acción no se puede deshacer.`)) return;
    this.deletingId.set(rol.id_rol);
    this.http.delete(`${this.api}/${rol.id_rol}`).subscribe({
      next: () => {
        this.roles.update(list => list.filter(r => r.id_rol !== rol.id_rol));
        if (this.rolEditando()?.id_rol === rol.id_rol) this.rolEditando.set(null);
        this.success.set('Rol eliminado');
        this.deletingId.set(null);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => {
        this.error.set(e.error?.detail ?? 'Error al eliminar rol');
        this.deletingId.set(null);
      },
    });
  }
}
