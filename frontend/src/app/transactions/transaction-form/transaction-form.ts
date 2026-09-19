import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { TransactionService } from '../../services/transaction';
import { AccountService, Account } from '../../services/account';
import { CategoryPicker } from '../../components/category-picker/category-picker';

@Component({
  selector: 'app-transaction-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule, CategoryPicker],
  templateUrl: './transaction-form.html',
  styleUrls: ['./transaction-form.scss']
})
export class TransactionForm implements OnInit {
  transactionForm: FormGroup;
  transactionId: string | null = null;
  isEditMode = false;
  accounts: Account[] = [];

  constructor(
    private fb: FormBuilder,
    private transactionService: TransactionService,
    private accountService: AccountService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.transactionForm = this.fb.group({
      account_id: ['', Validators.required],
      transaction_type: ['expense', Validators.required],
      description: ['', Validators.required],
      amount: ['', [Validators.required, Validators.min(0.01)]],
      transaction_date: [new Date().toISOString().split('T')[0], Validators.required],
      category_id: [null],
      to_account_id: [''],
      status: ['paid'],
      merchant: ['']
    });

    this.transactionForm.get('transaction_type')?.valueChanges.subscribe(type => {
      const toAccountCtrl = this.transactionForm.get('to_account_id');
      const catCtrl = this.transactionForm.get('category_id');
      if (type === 'transfer') {
        toAccountCtrl?.setValidators([Validators.required]);
        catCtrl?.clearValidators();
      } else {
        toAccountCtrl?.clearValidators();
      }
      toAccountCtrl?.updateValueAndValidity();
      catCtrl?.updateValueAndValidity();
    });
  }

  ngOnInit() {
    this.accountService.listAccounts().subscribe(data => this.accounts = data);

    this.transactionId = this.route.snapshot.paramMap.get('id');
    if (this.transactionId) {
      this.isEditMode = true;
      this.loadTransaction(this.transactionId);
    }
  }

  loadTransaction(id: string) {
    this.transactionService.getTransaction(id).subscribe(t => {
      this.transactionForm.patchValue(t);
    });
  }

  onSubmit() {
    if (this.transactionForm.valid) {
      const payload = this.transactionForm.value;

      const onComplete = {
        next: () => this.router.navigate(['/transactions']),
        error: (err: any) => console.error('Error saving transaction', err)
      };

      if (payload.transaction_type === 'transfer' && !this.isEditMode) {
        this.transactionService.createTransfer({
          from_account_id: payload.account_id,
          to_account_id: payload.to_account_id,
          amount: payload.amount,
          transaction_date: payload.transaction_date,
          description: payload.description
        }).subscribe(onComplete);
      } else {
        const request = this.isEditMode && this.transactionId
          ? this.transactionService.updateTransaction(this.transactionId, payload)
          : this.transactionService.createTransaction(payload);

        request.subscribe(onComplete);
      }
    }
  }
}
