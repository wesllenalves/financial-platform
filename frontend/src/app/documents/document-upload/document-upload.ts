import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { HttpEventType } from '@angular/common/http';
import { DocumentService } from '../../services/document';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './document-upload.html',
  styleUrls: ['./document-upload.scss']
})
export class DocumentUpload {
  selectedFile: File | null = null;
  progress = 0;
  message = '';
  isUploading = false;

  constructor(private documentService: DocumentService, private router: Router) {}

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0] ?? null;
  }

  upload(): void {
    if (!this.selectedFile) return;

    this.progress = 0;
    this.isUploading = true;
    this.message = '';

    this.documentService.uploadDocument(this.selectedFile).subscribe({
      next: (event: any) => {
        if (event.type === HttpEventType.UploadProgress) {
          this.progress = Math.round(100 * event.loaded / event.total);
        } else if (event.type === HttpEventType.Response) {
          this.message = 'Upload successful!';
          this.isUploading = false;
          // Navigate to review screen
          const docId = event.body.id;
          this.router.navigate(['/documents', docId, 'review']);
        }
      },
      error: (err: any) => {
        this.progress = 0;
        this.message = 'Could not upload the file: ' + (err.error?.error?.message || err.message);
        this.isUploading = false;
      }
    });
  }
}
