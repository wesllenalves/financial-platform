import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../core/api.service';
import { apiErrorMessage, formatMoney } from '../core/format';
import { Account, Category, Transaction } from '../core/models';

@Component({
  selector: 'app-transactions',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="container grid">
      <section class="panel">
        <h2>Novo lançamento</h2>
        @if (accounts().length === 0) {
          <p class="muted">Crie uma conta para começar a lançar transações.</p>
          <button style="width:auto" (click)="createDefaultAccount()">Criar conta corrente</button>
        } @else {
          <form class="grid cols-4" [formGroup]="form" (ngSubmit)="submit()">
            <div>
              <label for="type">Tipo</label>
              <select id="type" formControlName="transaction_type">
                <option value="expense">Despesa</option>
                <option value="income">Receita</option>
              </select>
            </div>
            <div>
              <label for="description">Descrição</label>
              <input id="description" formControlName="description" />
            </div>
            <div>
              <label for="amount">Valor</label>
              <input id="amount" type="number" step="0.01" min="0.01" formControlName="amount" />
            </div>
            <div>
              <label for="date">Data</label>
              <input id="date" type="date" formControlName="transaction_date" />
            </div>
            <div>
              <label for="account">Conta</label>
              <select id="account" formControlName="account_id">
                @for (account of accounts(); track account.id) {
                  <option [value]="account.id">{{ account.name }}</option>
                }
              </select>
            </div>
            <div>
              <label for="category">Categoria</label>
              <select id="category" formControlName="category_id">
                <option value="">Sem categoria</option>
                @for (category of visibleCategories(); track category.id) {
                  <option [value]="category.id">{{ category.name }}</option>
                }
              </select>
            </div>
            <div style="align-self:end">
              <button type="submit" [disabled]="form.invalid || saving()">Adicionar</button>
            </div>
          </form>
        }
        @if (error()) {
          <p class="error" style="margin-top:12px">{{ error() }}</p>
        }
      </section>

      <section class="panel">
        <h2>Lançamentos</h2>
        @if (transactions().length === 0) {
          <p class="muted">Nenhum lançamento ainda.</p>
        } @else {
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Categoria</th>
                <th class="num">Valor</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (item of transactions(); track item.id) {
                <tr>
                  <td>{{ item.transaction_date }}</td>
                  <td>{{ item.description }}</td>
                  <td>{{ categoryName(item.category_id) }}</td>
                  <td
                    class="num"
                    [class.positive]="item.transaction_type === 'income'"
                    [class.negative]="item.transaction_type === 'expense'"
                  >
                    {{ item.transaction_type === 'income' ? '+' : '−' }}{{ money(item.amount) }}
                  </td>
                  <td class="num">
                    <button class="ghost" style="width:auto" (click)="remove(item)">Excluir</button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        }
      </section>
    </div>
  `,
})
export class TransactionsComponent {
  private readonly api = inject(ApiService);

  readonly accounts = signal<Account[]>([]);
  readonly categories = signal<Category[]>([]);
  readonly transactions = signal<Transaction[]>([]);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly money = formatMoney;

  readonly form = inject(FormBuilder).nonNullable.group({
    account_id: ['', Validators.required],
    transaction_type: ['expense', Validators.required],
    description: ['', Validators.required],
    amount: [null as number | null, [Validators.required, Validators.min(0.01)]],
    transaction_date: [new Date().toISOString().slice(0, 10), Validators.required],
    category_id: [''],
  });

  readonly visibleCategories = computed(() =>
    this.categories().filter((category) => category.kind === this.form.getRawValue().transaction_type),
  );

  constructor() {
    this.reload();
    this.form.controls.transaction_type.valueChanges.subscribe(() =>
      this.form.controls.category_id.setValue(''),
    );
  }

  categoryName(id: string | null): string {
    return this.categories().find((category) => category.id === id)?.name ?? '—';
  }

  createDefaultAccount(): void {
    this.api
      .createAccount({ name: 'Conta Corrente', type: 'checking', opening_balance: '0.00' })
      .subscribe(() => this.reload());
  }

  submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    const value = this.form.getRawValue();
    this.api
      .createTransaction({
        ...value,
        amount: String(value.amount),
        category_id: value.category_id || null,
      })
      .subscribe({
        next: () => {
          this.form.patchValue({ description: '', amount: null });
          this.saving.set(false);
          this.reload();
        },
        error: (err) => {
          this.error.set(apiErrorMessage(err));
          this.saving.set(false);
        },
      });
  }

  remove(item: Transaction): void {
    this.api.deleteTransaction(item.id).subscribe(() => this.reload());
  }

  private reload(): void {
    this.api.accounts().subscribe((accounts) => {
      this.accounts.set(accounts);
      if (!this.form.getRawValue().account_id && accounts.length > 0) {
        this.form.controls.account_id.setValue(accounts[0].id);
      }
    });
    this.api.categories().subscribe((categories) => this.categories.set(categories));
    this.api.transactions({ limit: 50 }).subscribe((page) => this.transactions.set(page.items));
  }
}
