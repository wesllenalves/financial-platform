import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { apiErrorMessage } from '../core/format';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="container" style="max-width:420px">
      <h1>Entrar</h1>
      <form class="panel grid" [formGroup]="form" (ngSubmit)="submit()">
        <div>
          <label for="email">E-mail</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
        </div>
        <div>
          <label for="password">Senha</label>
          <input
            id="password"
            type="password"
            formControlName="password"
            autocomplete="current-password"
          />
        </div>
        @if (error()) {
          <p class="error">{{ error() }}</p>
        }
        <button type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Entrando…' : 'Entrar' }}
        </button>
        <p class="muted">Não tem conta? <a routerLink="/register">Criar conta</a></p>
      </form>
    </div>
  `,
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    const { email, password } = this.form.getRawValue();
    this.auth.login(email, password).subscribe({
      next: () => {
        this.auth.loadCurrentUser().subscribe({ error: () => undefined });
        void this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err));
        this.loading.set(false);
      },
    });
  }
}
