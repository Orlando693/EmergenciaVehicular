import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { UsuarioService } from '../../core/services/usuario.service';
import { BitacoraService } from '../../services/bitacora.service';

export interface DemoCredential {
  role: string;
  email: string;
  password: string;
  color: string;
  icon: string;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  form: FormGroup;
  loading = signal(false);
  error = signal('');
  success = signal('');
  showPassword = signal(false);
  isRegisterMode = signal(false);

  demoCredentials: DemoCredential[] = [
    { role: 'Administrador', email: 'admin@emergencia.com', password: 'Admin1234', color: 'blue', icon: '' },
  ];

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private usuarioService: UsuarioService,
    private router: Router,
    private bitacora: BitacoraService,
  ) {
    this.form = this.fb.group({
      nombres: [''],
      apellidos: [''],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      telefono: [''],
    });
  }

  toggleFormMode(isRegister: boolean) {
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

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.success.set('');

    if (this.isRegisterMode()) {
      const payload = {
        ...this.form.value,
        rol: 'CLIENTE'
      };

      this.usuarioService.registrar(payload).subscribe({
        next: () => {
          this.success.set('¡Cuenta de cliente creada exitosamente! Ahora puedes iniciar sesión.');
          this.loading.set(false);
          this.toggleFormMode(false);
        },
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Error al registrar la cuenta');
          this.loading.set(false);
        }
      });
    } else {
      const loginPayload = {
        email: this.form.value.email,
        password: this.form.value.password
      };

      this.auth.login(loginPayload).subscribe({
        next: () => {
          this.bitacora.logAction('Autenticación', `Inicio de sesión: ${this.form.value.email}`).subscribe();
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          this.error.set(err.error?.detail ?? 'Error al iniciar sesión');
          this.loading.set(false);
        },
      });
    }
  }

  fillCredential(cred: DemoCredential) {
    if (this.isRegisterMode()) this.toggleFormMode(false);
    this.form.patchValue({ email: cred.email, password: cred.password });
    this.error.set('');
  }

  togglePassword() {
    this.showPassword.update(v => !v);
  }

  get emailCtrl() { return this.form.get('email')!; }
  get passwordCtrl() { return this.form.get('password')!; }
  get nombresCtrl() { return this.form.get('nombres')!; }
  get apellidosCtrl() { return this.form.get('apellidos')!; }
}
