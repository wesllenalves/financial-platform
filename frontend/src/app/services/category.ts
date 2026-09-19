import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Category {
  id: string;
  name: string;
  kind: 'income' | 'expense';
  parent_id: string | null;
  essentiality: string | null;
  system: boolean;
  archived: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private readonly API_URL = `${environment.apiUrl}/categories`;

  constructor(private http: HttpClient) {}

  listCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(this.API_URL);
  }
}
