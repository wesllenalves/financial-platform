import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AccountService } from '../../services/account';

@Component({
  selector: 'app-account-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './account-form.html',
  styleUrls: ['./account-form.scss']
})
export class AccountForm implements OnInit {
  accountForm: FormGroup;
  accountId: string | null = null;
  isEditMode = false;

  accountTypes = ['checking', 'savings', 'cash', 'credit_card', 'investment'];

  constructor(
    private fb: FormBuilder,
    private accountService: AccountService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.accountForm = this.fb.group({
      name: ['', Validators.required],
      type: ['checking', Validators.required],
      opening_balance: ['0.00', Validators.required],
      institution: [''],
      active: [true]
    });
  }

  ngOnInit() {
    this.accountId = this.route.snapshot.paramMap.get('id');
    if (this.accountId) {
      this.isEditMode = true;
      this.loadAccount(this.accountId);
    }
  }

  loadAccount(id: string) {
    this.accountService.getAccount(id).subscribe(account => {
      this.accountForm.patchValue(account);
    });
  }

  onSubmit() {
    if (this.accountForm.valid) {
      const payload = this.accountForm.value;
      const request = this.isEditMode && this.accountId
        ? this.accountService.updateAccount(this.accountId, payload)
        : this.accountService.createAccount(payload);

      request.subscribe({
        next: () => this.router.navigate(['/accounts']),
        error: (err) => console.error('Error saving account', err)
      });
    }
  }
}
