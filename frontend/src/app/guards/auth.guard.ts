import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): boolean {
    
    // Auth mock: In a real scenario, check AuthService authentication state
    const isAuthenticated = true; // Set to true to allow access during dev testing
    
    if (isAuthenticated) {
      return true;
    } else {
      this.router.navigate(['/admin/login']);
      return false;
    }
  }
}
