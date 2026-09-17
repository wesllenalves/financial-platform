import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    @if (auth.isAuthenticated()) {
      <nav class="top">
        <strong>Financial Platform</strong>
        <a routerLink="/dashboard" routerLinkActive="active">Painel</a>
        <a routerLink="/transactions" routerLinkActive="active">Transações</a>
        <span class="spacer"></span>
        <span class="muted">{{ auth.currentUser()?.email }}</span>
        <button class="ghost" style="width:auto" (click)="auth.logout()">Sair</button>
      </nav>
    }
    <router-outlet />
  `,
})
export class AppComponent {
  readonly auth = inject(AuthService);

  constructor() {
    if (this.auth.isAuthenticated()) {
      this.auth.loadCurrentUser().subscribe({ error: () => undefined });
    }
  }
}
