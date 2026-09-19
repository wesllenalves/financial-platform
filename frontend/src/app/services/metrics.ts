import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PeriodSummary {
  period: string;
  partial: boolean;
  income: string;
  expenses: string;
  net_cash_flow: string;
  savings_rate: string | null;
}

export interface CategoryTotal {
  category_id: string | null;
  category_name: string;
  total: string;
  share: string | null;
}

export interface TrendPoint {
  period: string;
  income: string;
  expenses: string;
}

export interface UpcomingBill {
  id: string;
  description: string;
  amount: string;
  due_date: string;
  status: string;
}

export interface Dashboard {
  current_balance: string;
  total_debt: string;
  summary: PeriodSummary;
  previous_summary: PeriodSummary;
  by_category: CategoryTotal[];
  trend: TrendPoint[];
  upcoming_bills: UpcomingBill[];
}

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
  private readonly API_URL = `${environment.apiUrl}/analysis`;

  constructor(private http: HttpClient) {}

  getDashboard(period?: string): Observable<Dashboard> {
    let params = new HttpParams();
    if (period) {
      params = params.set('period', period);
    }
    return this.http.get<Dashboard>(`${this.API_URL}/dashboard`, { params });
  }
}
