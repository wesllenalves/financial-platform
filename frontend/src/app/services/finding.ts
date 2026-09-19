import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Finding {
  id: string;
  rule_id: string;
  period: string;
  severity: string;
  title: string;
  evidence: any;
  estimated_monthly_impact: string | null;
}

export interface AnalysisResponse {
  message: string;
  findings_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class FindingService {
  private readonly API_URL = environment.apiUrl;

  constructor(private http: HttpClient) {}

  runAnalysis(period?: string): Observable<AnalysisResponse> {
    let params = new HttpParams();
    if (period) {
      params = params.set('period', period);
    }
    return this.http.post<AnalysisResponse>(`${this.API_URL}/analysis/run`, null, { params });
  }

  listFindings(limit: number = 50, offset: number = 0): Observable<Finding[]> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    return this.http.get<Finding[]>(`${this.API_URL}/findings`, { params });
  }
}
