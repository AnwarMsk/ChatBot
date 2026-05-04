import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  password = '';
  error = '';

  constructor(private router: Router) {}

  login() {
    // Basic mock logic. In real app, connect to AuthService.
    if (this.password === 'admin') {
      this.router.navigate(['/admin/dashboard']);
    } else {
      this.error = 'Mot de passe incorrect (indice: admin)';
    }
  }
}
