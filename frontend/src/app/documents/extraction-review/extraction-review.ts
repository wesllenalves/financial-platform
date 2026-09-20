import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { DocumentService, ExtractedItem, Document } from '../../services/document';
import { AccountService, Account } from '../../services/account';
import { CategoryPicker } from '../../components/category-picker/category-picker';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-extraction-review',
  standalone: true,
  imports: [CommonModule, RouterModule, CategoryPicker, FormsModule],
  templateUrl: './extraction-review.html',
  styleUrls: ['./extraction-review.scss']
})
export class ExtractionReview implements OnInit {
  documentId: string | null = null;
  document: Document | null = null;
  items: any[] = [];
  accounts: Account[] = [];

  constructor(
    private documentService: DocumentService,
    private accountService: AccountService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit() {
    this.accountService.listAccounts().subscribe(data => this.accounts = data);
    this.documentId = this.route.snapshot.paramMap.get('id');

    if (this.documentId) {
      this.documentService.getDocument(this.documentId).subscribe(doc => this.document = doc);
      this.loadItems();
    }
  }

  loadItems() {
    if (this.documentId) {
      this.documentService.getExtractedItems(this.documentId).subscribe(data => {
        // Map to add form state
        this.items = data.map(item => ({
          ...item,
          override: {
            account_id: '',
            transaction_type: 'expense',
            description: item.normalized_payload.description,
            amount: item.normalized_payload.amount,
            transaction_date: item.normalized_payload.transaction_date,
            merchant: item.normalized_payload.merchant,
            category_id: null,
            status: 'paid'
          }
        }));
      });
    }
  }

  confirm(item: any) {
    if (!item.override.account_id) {
      alert("Please select an account.");
      return;
    }

    this.documentService.confirmExtraction(item.id, item.override).subscribe({
      next: () => {
        item.status = 'edited_confirmed';
        this.checkAllDone();
      },
      error: (err) => console.error(err)
    });
  }

  reject(item: any) {
    if (confirm("Are you sure you want to reject this extraction?")) {
      this.documentService.rejectExtraction(item.id).subscribe({
        next: () => {
          item.status = 'rejected';
          this.checkAllDone();
        },
        error: (err) => console.error(err)
      });
    }
  }

  checkAllDone() {
    const allDone = this.items.every(i => i.status === 'edited_confirmed' || i.status === 'rejected' || i.status === 'confirmed');
    if (allDone) {
      setTimeout(() => this.router.navigate(['/transactions']), 1000);
    }
  }
}
