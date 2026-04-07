import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { UsuarioService } from '../../../core/services/usuario.service';
import { AuthService } from '../../../core/services/auth.service';
import { Usuario } from '../../../models/usuario.model';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './perfil.component.html',
  styleUrl: './perfil.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class PerfilComponent implements OnInit {
  usuario  = signal<Usuario | null>(null);
  loading  = signal(true);
  success  = signal('');
  error    = signal('');
  saving   = signal(false);

  form: FormGroup;
  pwForm: FormGroup;

  constructor(
    private srv: UsuarioService,
    public auth: AuthService,
    private fb: FormBuilder,
  ) {
    this.form = this.fb.group({
      nombres:   ['', Validators.required],
      apellidos: ['', Validators.required],
      telefono:  [''],
    });
    this.pwForm = this.fb.group({
      password_actual: ['', Validators.required],
      password_nuevo:  ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  ngOnInit() {
    this.srv.miPerfil().subscribe({
      next: (u) => {
        this.usuario.set(u);
        this.form.patchValue({ nombres: u.nombres, apellidos: u.apellidos, telefono: u.telefono });
        this.loading.set(false);
      },
      error: () => { this.error.set('Error al cargar perfil'); this.loading.set(false); },
    });
  }

  guardarPerfil() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    this.srv.actualizarPerfil(this.form.value).subscribe({
      next: (u) => {
        this.usuario.set(u);
        this.success.set('Perfil actualizado correctamente');
        this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error'); this.saving.set(false); },
    });
  }

  cambiarPassword() {
    if (this.pwForm.invalid) { this.pwForm.markAllAsTouched(); return; }
    this.saving.set(true);
    this.srv.actualizarPerfil(this.pwForm.value).subscribe({
      next: () => {
        this.success.set('Contraseña actualizada');
        this.pwForm.reset();
        this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error'); this.saving.set(false); },
    });
  }
}
