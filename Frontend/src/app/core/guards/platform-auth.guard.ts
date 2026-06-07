import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PlatformAuthService } from '../services/platform-auth.service';

export const platformAuthGuard: CanActivateFn = () => {
  const auth = inject(PlatformAuthService);
  const router = inject(Router);
  if (auth.isAuthenticated()) return true;
  router.navigate(['/platform/login']);
  return false;
};

export const platformGuestGuard: CanActivateFn = () => {
  const auth = inject(PlatformAuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return true;
  router.navigate(['/platform/dashboard']);
  return false;
};
