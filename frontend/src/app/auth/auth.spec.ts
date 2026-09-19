import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AuthService } from './auth';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should authenticate user on successful login', () => {
    const mockToken = {
      access_token: 'access123',
      refresh_token: 'refresh123',
      token_type: 'bearer'
    };

    service.login({ email: 'test@test.com', password: 'password' }).subscribe();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/auth/login');
    expect(req.request.method).toBe('POST');
    req.flush(mockToken);

    expect(service.getAccessToken()).toBe('access123');
    expect(localStorage.getItem('refresh_token')).toBe('refresh123');
  });
});
