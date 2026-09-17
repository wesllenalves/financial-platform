import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Account, Category, Dashboard, Page, Transaction } from './models';

export interface TransactionQuery {
  date_from?: string;
  date_to?: string;
  transaction_type?: string;
  category_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  accounts(): Observable<Account[]> {
    return this.http.get<Account[]>('/api/v1/accounts');
  }

  createAccount(body: {
    name: string;
    type: string;
    opening_balance: string;
  }): Observable<Account> {
    return this.http.post<Account>('/api/v1/accounts', body);
  }

  categories(): Observable<Category[]> {
    return this.http.get<Category[]>('/api/v1/categories');
  }

  transactions(query: TransactionQuery = {}): Observable<Page<Transaction>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<Page<Transaction>>('/api/v1/transactions', { params });
  }

  createTransaction(body: Record<string, unknown>): Observable<Transaction> {
    return this.http.post<Transaction>('/api/v1/transactions', body);
  }

  deleteTransaction(id: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/transactions/${id}`);
  }

  dashboard(period?: string): Observable<Dashboard> {
    const params = period ? new HttpParams().set('period', period) : undefined;
    return this.http.get<Dashboard>('/api/v1/analysis/dashboard', { params });
  }
}
