import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Account {
  id: string;
  name: string;
  type: string;
  opening_balance: string;
  institution: string | null;
  active: boolean;
  current_balance?: string; // from AccountBalanceOut
}

export interface AccountCreate {
  name: string;
  type: string;
  opening_balance?: string;
  institution?: string;
}

export interface AccountUpdate {
  name?: string;
  institution?: string;
  opening_balance?: string;
  active?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AccountService {
  private readonly API_URL = `${environment.apiUrl}/accounts`;

  constructor(private http: HttpClient) {}

  listAccounts(): Observable<Account[]> {
    return this.http.get<Account[]>(this.API_URL);
  }

  getAccount(id: string): Observable<Account> {
    return this.http.get<Account>(`${this.API_URL}/${id}`);
  }

  createAccount(data: AccountCreate): Observable<Account> {
    return this.http.post<Account>(this.API_URL, data);
  }

  updateAccount(id: string, data: AccountUpdate): Observable<Account> {
    return this.http.patch<Account>(`${this.API_URL}/${id}`, data);
  }

  deleteAccount(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/${id}`);
  }
}
