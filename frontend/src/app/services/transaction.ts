import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Transaction {
  id: string;
  account_id: string;
  category_id: string | null;
  transaction_type: 'income' | 'expense';
  description: string;
  amount: string;
  transaction_date: string;
  status: string;
  merchant: string | null;
}

export interface TransactionCreate {
  account_id: string;
  transaction_type: 'income' | 'expense';
  description: string;
  amount: string;
  transaction_date: string;
  category_id?: string | null;
  status?: string;
  merchant?: string | null;
}

export interface TransactionFilters {
  date_from?: string;
  date_to?: string;
  category_id?: string;
  account_id?: string;
  transaction_type?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

@Injectable({
  providedIn: 'root'
})
export class TransactionService {
  private readonly API_URL = `${environment.apiUrl}/transactions`;

  constructor(private http: HttpClient) {}

  listTransactions(filters: TransactionFilters = {}): Observable<Page<Transaction>> {
    let params = new HttpParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, value.toString());
      }
    });
    return this.http.get<Page<Transaction>>(this.API_URL, { params });
  }

  getTransaction(id: string): Observable<Transaction> {
    return this.http.get<Transaction>(`${this.API_URL}/${id}`);
  }

  createTransaction(data: TransactionCreate): Observable<Transaction> {
    return this.http.post<Transaction>(this.API_URL, data);
  }

  createTransfer(data: any): Observable<Transaction[]> {
    return this.http.post<Transaction[]>(`${this.API_URL}/transfers`, data);
  }

  updateTransaction(id: string, data: Partial<TransactionCreate>): Observable<Transaction> {
    return this.http.patch<Transaction>(`${this.API_URL}/${id}`, data);
  }

  deleteTransaction(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API_URL}/${id}`);
  }
}
