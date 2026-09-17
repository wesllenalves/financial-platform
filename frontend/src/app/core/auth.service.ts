import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

import { AuthTokens, User } from './models';

const ACCESS_KEY = 'fp.access';
const REFRESH_KEY = 'fp.refresh';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser = signal<User | null>(null);
  readonly isAuthenticated = computed(() => this.accessToken() !== null);

  private readonly token = signal<string | null>(localStorage.getItem(ACCESS_KEY));

  accessToken(): string | null {
    return this.token();
  }

  register(name: string, email: string, password: string): Observable<User> {
    return this.http.post<User>('/api/v1/auth/register', { name, email, password });
  }

  login(email: string, password: string): Observable<AuthTokens> {
    return this.http
      .post<AuthTokens>('/api/v1/auth/login', { email, password })
      .pipe(tap((tokens) => this.store(tokens)));
  }

  loadCurrentUser(): Observable<User> {
    return this.http.get<User>('/api/v1/users/me').pipe(tap((user) => this.currentUser.set(user)));
  }

  logout(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    this.token.set(null);
    this.currentUser.set(null);
    void this.router.navigate(['/login']);
  }

  private store(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
    this.token.set(tokens.access_token);
  }
}
