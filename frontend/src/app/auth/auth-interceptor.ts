import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth';
import { catchError, switchMap } from 'rxjs/operators';
import { throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();

  let authReq = req;
  if (token) {
    authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }

  return next(authReq).pipe(
    catchError(error => {
      // Prevent infinite loop if the refresh token call itself returns 401
      if (error.status === 401 && token && !req.url.includes('/refresh')) {
        return authService.refreshToken().pipe(
          switchMap((tokens) => {
            const newAuthReq = req.clone({
              setHeaders: { Authorization: `Bearer ${tokens.access_token}` }
            });
            return next(newAuthReq);
          })
        );
      }
      return throwError(() => error);
    })
  );
};
