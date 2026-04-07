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
  roles     = signal<Rol[]>([]);
  permisos  = signal<Permiso[]>([]);
  loading   = signal(true);
  showForm  = signal(false);
  success   = signal('');
  error     = signal('');
  saving    = signal(false);

  form: FormGroup;
  private api = `${environment.apiUrl}/roles`;

  constructor(private http: HttpClient, private fb: FormBuilder) {
    this.form = this.fb.group({
      nombre:      ['', Validators.required],
      descripcion: [''],
    });
  }

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    this.http.get<Rol[]>(this.api).subscribe({
      next: (r) => { this.roles.set(r); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar roles'); this.loading.set(false); },
    });
    this.http.get<Permiso[]>(`${this.api}/permisos`).subscribe({
      next: (p) => this.permisos.set(p),
    });
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    this.http.post<Rol>(this.api, this.form.value).subscribe({
      next: () => {
        this.success.set('Rol creado'); this.showForm.set(false);
        this.form.reset(); this.cargar(); this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error'); this.saving.set(false); },
    });
  }
}
