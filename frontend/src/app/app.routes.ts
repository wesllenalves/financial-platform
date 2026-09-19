import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Register } from './register/register';
import { Shell } from './shell/shell';
import { authGuard } from './auth/auth-guard';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      // other authenticated routes will go here
    ]
  },
  { path: '**', redirectTo: '' }
];
