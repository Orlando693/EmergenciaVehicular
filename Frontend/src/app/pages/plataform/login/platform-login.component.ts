import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { PlatformAuthService } from '../../../core/services/platform-auth.service';

@Component({
  selector: 'app-platform-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './platform-login.component.html',
  styleUrls: ['./platform-login.component.css'],
})
export class PlatformLoginComponent {
  email    = '';
  password = '';
  showPass = signal(false);
  loading  = signal(false);
  error    = signal('');

  constructor(private auth: PlatformAuthService, private router: Router) {}

  useDemo() {
    this.email    = 'superadmin@emergencia.com';
    this.password = 'SuperAdmin1234';
  }

  submit() {
    this.error.set('');
    if (!this.email || !this.password) {
      this.error.set('Ingresa correo y contraseña.');
      return;
    }
    this.loading.set(true);
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigate(['/platform/dashboard']),
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'Credenciales incorrectas.');
      },
    });
  }
}
