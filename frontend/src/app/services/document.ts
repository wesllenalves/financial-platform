import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ExtractedItem {
  id: string;
  document_id: string;
  raw_payload: any;
  normalized_payload: any;
  field_confidence: any;
  duplicate_of_transaction_id: string | null;
  duplicate_reason: string | null;
  status: string;
}

export interface Document {
  id: string;
  filename: string;
  processing_status: string;
  error_message: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private readonly API_URL = `${environment.apiUrl}/documents`;

  constructor(private http: HttpClient) {}

  uploadDocument(file: File): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);

    const req = new HttpRequest('POST', `${this.API_URL}/upload`, formData, {
      reportProgress: true,
      responseType: 'json'
    });

    return this.http.request(req);
  }

  getDocument(id: string): Observable<Document> {
    return this.http.get<Document>(`${this.API_URL}/${id}`);
  }

  getExtractedItems(docId: string): Observable<ExtractedItem[]> {
    return this.http.get<ExtractedItem[]>(`${this.API_URL}/${docId}/items`);
  }

  confirmExtraction(itemId: string, transactionOverride: any): Observable<ExtractedItem> {
    return this.http.post<ExtractedItem>(`${this.API_URL}/items/${itemId}/confirm`, {
      transaction_override: transactionOverride
    });
  }

  rejectExtraction(itemId: string): Observable<ExtractedItem> {
    return this.http.post<ExtractedItem>(`${this.API_URL}/items/${itemId}/reject`, {});
  }
}
