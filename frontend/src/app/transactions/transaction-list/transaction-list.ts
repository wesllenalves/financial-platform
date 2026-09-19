import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TransactionService, Transaction } from '../../services/transaction';
import { AccountService, Account } from '../../services/account';
import { CategoryPicker } from '../../components/category-picker/category-picker';

@Component({
  selector: 'app-transaction-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, CategoryPicker],
  templateUrl: './transaction-list.html',
  styleUrls: ['./transaction-list.scss']
})
export class TransactionList implements OnInit {
  transactions: Transaction[] = [];
  accounts: Account[] = [];
  total = 0;
  limit = 50;
  offset = 0;

  filterForm: FormGroup;

  constructor(
    private transactionService: TransactionService,
    private accountService: AccountService,
    private fb: FormBuilder
  ) {
    this.filterForm = this.fb.group({
      search: [''],
      date_from: [''],
      date_to: [''],
      transaction_type: [''],
      account_id: [''],
      category_id: [''],
      status: ['']
    });
  }

  ngOnInit() {
    this.loadAccounts();
    this.loadTransactions();

    this.filterForm.valueChanges.subscribe(() => {
      this.offset = 0; // reset pagination on filter change
      this.loadTransactions();
    });
  }

  loadAccounts() {
    this.accountService.listAccounts().subscribe(data => this.accounts = data);
  }

  loadTransactions() {
    const filters = {
      ...this.filterForm.value,
      limit: this.limit,
      offset: this.offset
    };
    this.transactionService.listTransactions(filters).subscribe({
      next: (data) => {
        this.transactions = data.items;
        this.total = data.total;
      }
    });
  }

  nextPage() {
    if (this.offset + this.limit < this.total) {
      this.offset += this.limit;
      this.loadTransactions();
    }
  }

  prevPage() {
    if (this.offset > 0) {
      this.offset -= this.limit;
      this.loadTransactions();
    }
  }

  deleteTransaction(id: string) {
    if (confirm('Are you sure?')) {
      this.transactionService.deleteTransaction(id).subscribe(() => {
        this.loadTransactions();
      });
    }
  }
}
