import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Register } from './register/register';
import { Shell } from './shell/shell';
import { authGuard } from './auth/auth-guard';
import { AccountList } from './accounts/account-list/account-list';
import { AccountForm } from './accounts/account-form/account-form';
import { TransactionList } from './transactions/transaction-list/transaction-list';
import { TransactionForm } from './transactions/transaction-form/transaction-form';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: 'accounts', component: AccountList },
      { path: 'accounts/new', component: AccountForm },
      { path: 'accounts/:id/edit', component: AccountForm },
      { path: 'transactions', component: TransactionList },
      { path: 'transactions/new', component: TransactionForm },
      { path: 'transactions/:id/edit', component: TransactionForm },
      { path: '', redirectTo: 'transactions', pathMatch: 'full' }
    ]
  },
  { path: '**', redirectTo: '' }
];
