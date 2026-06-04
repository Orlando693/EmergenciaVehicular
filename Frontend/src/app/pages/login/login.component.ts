import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { BitacoraService } from '../../services/bitacora.service';

type Pantalla = 'workspace' | 'credenciales';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, FormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  pantalla = signal<Pantalla>('workspace');
  isRegisterMode = signal(false);

  workspaceSlug = '';
  workspaceNombre = signal('');
  loadingWorkspace = signal(false);
  errorWorkspace = signal('');

  form: FormGroup;
  loading = signal(false);
  error = signal('');
  success = signal('');
  showPassword = signal(false);

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private usuarioService: UsuarioService,
    private router: Router,
    private bitacora: BitacoraService,
  ) {
    this.form = this.fb.group({
      nombres:   [''],
      apellidos: [''],
      email:     ['', [Validators.required, Validators.email]],
      password:  ['', [Validators.required, Validators.minLength(6)]],
      telefono:  [''],
    });
  }

  /* ─── Paso 1: workspace ─── */

  continuarWorkspace(): void {
    const slug = this.workspaceSlug.trim().toLowerCase();
    if (!slug) { this.errorWorkspace.set('Ingresa el nombre del workspace'); return; }

    this.loadingWorkspace.set(true);
    this.errorWorkspace.set('');

    this.auth.verificarWorkspace(slug).subscribe({
      next: (info) => {
        this.workspaceNombre.set(info.nombre);
        this.workspaceSlug = info.slug;
        this.pantalla.set('credenciales');
        this.loadingWorkspace.set(false);
      },
      error: () => {
        this.errorWorkspace.set('Workspace no encontrado. Verifica el nombre e intenta de nuevo.');
        this.loadingWorkspace.set(false);
      }
    });
  }

  volverAWorkspace(): void {
    this.pantalla.set('workspace');
    this.workspaceNombre.set('');
    this.error.set('');
    this.success.set('');
    this.form.reset();
    this.isRegisterMode.set(false);
  }

  /* ─── Paso 2: credenciales ─── */

  toggleFormMode(isRegister: boolean): void {
    this.isRegisterMode.set(isRegister);
    this.error.set('');
    this.success.set('');
    this.form.reset();

    if (isRegister) {
      this.form.get('nombres')?.setValidators([Validators.required]);
      this.form.get('apellidos')?.setValidators([Validators.required]);
    } else {
      this.form.get('nombres')?.clearValidators();
      this.form.get('apellidos')?.clearValidators();
    }
    this.form.get('nombres')?.updateValueAndValidity();
    this.form.get('apellidos')?.updateValueAndValidity();
  }

  submit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.loading.set(true);
    this.error.set('');
    this.success.set('');

    if (this.isRegisterMode()) {
      const payload = { ...this.form.value, rol: 'CLIENTE', tenant_slug: this.workspaceSlug };
      this.usuarioService.registrar(payload).subscribe({
        next: () => {
          this.success.set('¡Cuenta creada! Ahora puedes iniciar sesión.');
          this.loading.set(false);
          this.toggleFormMode(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Error al registrar la cuenta');
          this.loading.set(false);
        }
      });
    } else {
      this.auth.login({ email: this.form.value.email, password: this.form.value.password, tenant_slug: this.workspaceSlug }).subscribe({
        next: () => {
          this.bitacora.logAction('Autenticación', `Inicio de sesión: ${this.form.value.email}`).subscribe();
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Credenciales incorrectas');
          this.loading.set(false);
        },
      });
    }
  }

  usarCredencialDemo(email: string, password: string): void {
    this.form.patchValue({ email, password });
    this.error.set('');
  }

  togglePassword(): void { this.showPassword.update(v => !v); }

  get emailCtrl()     { return this.form.get('email')!; }
  get passwordCtrl()  { return this.form.get('password')!; }
  get nombresCtrl()   { return this.form.get('nombres')!; }
  get apellidosCtrl() { return this.form.get('apellidos')!; }
}
