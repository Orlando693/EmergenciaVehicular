import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { UsuarioService } from '../../../core/services/usuario.service';
import { Usuario, UsuarioCreate } from '../../../models/usuario.model';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './usuarios.component.html',
  styleUrl: './usuarios.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class UsuariosComponent implements OnInit {
  usuarios = signal<Usuario[]>([]);
  loading = signal(true);
  showForm = signal(false);
  error = signal('');
  success = signal('');
  saving = signal(false);

  form: FormGroup;

  constructor(private srv: UsuarioService, private fb: FormBuilder) {
    this.form = this.fb.group({
      nombres:   ['', Validators.required],
      apellidos: ['', Validators.required],
      email:     ['', [Validators.required, Validators.email]],
      password:  ['', [Validators.required, Validators.minLength(6)]],
      telefono:  [''],
      rol:       ['CLIENTE', Validators.required],
    });
  }

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    this.srv.listar().subscribe({
      next: (data) => { this.usuarios.set(data); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar usuarios'); this.loading.set(false); },
    });
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const data: UsuarioCreate = this.form.value;
    this.srv.registrar(data).subscribe({
      next: () => {
        this.success.set('Usuario creado correctamente');
        this.showForm.set(false);
        this.form.reset({ rol: 'CLIENTE' });
        this.cargar();
        this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al crear usuario');
        this.saving.set(false);
      },
    });
  }

  toggleEstado(u: Usuario) {
    const nuevoEstado = u.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    this.srv.cambiarEstado(u.id_usuario, nuevoEstado).subscribe({
      next: () => this.cargar(),
      error: (err) => this.error.set(err.error?.detail ?? 'Error al cambiar estado'),
    });
  }
}
