import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { apiErrorMessage } from '../core/format';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="container" style="max-width:420px">
      <h1>Criar conta</h1>
      <form class="panel grid" [formGroup]="form" (ngSubmit)="submit()">
        <div>
          <label for="name">Nome</label>
          <input id="name" formControlName="name" autocomplete="name" />
        </div>
        <div>
          <label for="email">E-mail</label>
          <input id="email" type="email" formControlName="email" autocomplete="email" />
        </div>
        <div>
          <label for="password">Senha (mínimo 8 caracteres)</label>
          <input
            id="password"
            type="password"
            formControlName="password"
            autocomplete="new-password"
          />
        </div>
        @if (error()) {
          <p class="error">{{ error() }}</p>
        }
        <button type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Criando…' : 'Criar conta' }}
        </button>
        <p class="muted">Já tem conta? <a routerLink="/login">Entrar</a></p>
      </form>
    </div>
  `,
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    const { name, email, password } = this.form.getRawValue();
    this.auth.register(name, email, password).subscribe({
      next: () =>
        this.auth.login(email, password).subscribe({
          next: () => {
            this.auth.loadCurrentUser().subscribe({ error: () => undefined });
            void this.router.navigate(['/dashboard']);
          },
          error: (err) => {
            this.error.set(apiErrorMessage(err));
            this.loading.set(false);
          },
        }),
      error: (err) => {
        this.error.set(apiErrorMessage(err));
        this.loading.set(false);
      },
    });
  }
}
