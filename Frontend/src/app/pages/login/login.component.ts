import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

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
  showPassword = signal(false);

  demoCredentials: DemoCredential[] = [
    { role: 'Administrador', email: 'admin@emergencia.com', password: 'Admin1234', color: 'blue', icon: '' },
  ];

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
  ) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set('');

    this.auth.login(this.form.value).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al iniciar sesión');
        this.loading.set(false);
      },
    });
  }

  fillCredential(cred: DemoCredential) {
    this.form.patchValue({ email: cred.email, password: cred.password });
    this.error.set('');
  }

  togglePassword() {
    this.showPassword.update(v => !v);
  }

  get emailCtrl() { return this.form.get('email')!; }
  get passwordCtrl() { return this.form.get('password')!; }
}
