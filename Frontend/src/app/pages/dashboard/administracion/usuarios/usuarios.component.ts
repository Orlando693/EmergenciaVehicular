import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { UsuarioService } from '../../../../core/services/usuario.service';
import { Usuario, UsuarioCreate, UsuarioUpdate } from '../../../../models/usuario.model';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './usuarios.component.html',
  styleUrl: './usuarios.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class UsuariosComponent implements OnInit {
  usuarios   = signal<Usuario[]>([]);
  loading    = signal(true);
  showForm   = signal(false);
  error      = signal('');
  success    = signal('');
  saving     = signal(false);

  usuarioEditando = signal<Usuario | null>(null);
  savingEdit      = signal(false);

  form:     FormGroup;
  editForm: FormGroup;

  constructor(private srv: UsuarioService, private fb: FormBuilder) {
    this.form = this.fb.group({
      nombres:   ['', Validators.required],
      apellidos: ['', Validators.required],
      email:     ['', [Validators.required, Validators.email]],
      password:  ['', [Validators.required, Validators.minLength(6)]],
      telefono:  [''],
      rol:       ['CLIENTE', Validators.required],
    });
    this.editForm = this.fb.group({
      nombres:   ['', Validators.required],
      apellidos: ['', Validators.required],
      telefono:  [''],
    });
  }

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    this.srv.listar().subscribe({
      next:  (data) => { this.usuarios.set(data); this.loading.set(false); },
      error: ()     => { this.error.set('Error al cargar usuarios'); this.loading.set(false); },
    });
  }

  hasError(ctrl: string, err: string): boolean {
    const c = this.form.get(ctrl);
    return !!(c && c.touched && c.hasError(err));
  }

  abrirNuevo() {
    this.form.reset({ rol: 'CLIENTE' });
    this.error.set('');
    this.showForm.set(true);
    this.usuarioEditando.set(null);
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    this.error.set('');
    const data: UsuarioCreate = this.form.value;
    this.srv.registrar(data).subscribe({
      next: (newUser: Usuario) => {
        this.success.set('Usuario creado correctamente');
        this.showForm.set(false);
        this.form.reset({ rol: 'CLIENTE' });
        this.usuarios.update(list => [newUser, ...list]);
        this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al crear usuario');
        this.saving.set(false);
      },
    });
  }

  abrirEdicion(u: Usuario) {
    this.usuarioEditando.set(u);
    this.editForm.patchValue({
      nombres:   u.nombres,
      apellidos: u.apellidos,
      telefono:  u.telefono ?? '',
    });
    this.error.set('');
    this.showForm.set(false);
  }

  cerrarEdicion() {
    this.usuarioEditando.set(null);
    this.error.set('');
  }

  guardarEdicion() {
    if (this.editForm.invalid) { this.editForm.markAllAsTouched(); return; }
    const u = this.usuarioEditando();
    if (!u) return;
    this.savingEdit.set(true);
    this.error.set('');
    const data: UsuarioUpdate = this.editForm.value;
    this.srv.actualizar(u.id_usuario, data).subscribe({
      next: (updated) => {
        this.usuarios.update(list => list.map(x => x.id_usuario === u.id_usuario ? updated : x));
        this.success.set('Usuario actualizado correctamente');
        this.usuarioEditando.set(null);
        this.savingEdit.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al actualizar usuario');
        this.savingEdit.set(false);
      },
    });
  }

  toggleEstado(u: Usuario) {
    const nuevoEstado = u.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    this.srv.cambiarEstado(u.id_usuario, nuevoEstado).subscribe({
      next: (updated) => this.usuarios.update(list => list.map(x => x.id_usuario === u.id_usuario ? updated : x)),
      error: (err) => this.error.set(err.error?.detail ?? 'Error al cambiar estado'),
    });
  }
}
