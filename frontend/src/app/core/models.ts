export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  currency: string;
}

export type TransactionType = 'income' | 'expense' | 'transfer';

export interface Account {
  id: string;
  name: string;
  type: string;
  opening_balance: string;
  current_balance: string;
  institution: string | null;
  active: boolean;
}

export interface Category {
  id: string;
  name: string;
  kind: 'income' | 'expense';
  parent_id: string | null;
  essentiality: string | null;
}

export interface Transaction {
  id: string;
  account_id: string;
  category_id: string | null;
  transaction_type: TransactionType;
  description: string;
  amount: string;
  transaction_date: string;
  merchant: string | null;
  status: string;
  source: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface PeriodSummary {
  period: string;
  partial: boolean;
  income: string;
  expenses: string;
  net_cash_flow: string;
  savings_rate: string | null;
}

export interface CategoryTotal {
  category_id: string | null;
  category_name: string;
  total: string;
  share: string;
}

export interface TrendPoint {
  period: string;
  income: string;
  expenses: string;
}

export interface RecurringSeries {
  merchant_key: string;
  description: string;
  occurrences: number;
  mean_amount: string;
  last_date: string;
  active: boolean;
}

export interface Dashboard {
  current_balance: string;
  total_debt: string;
  summary: PeriodSummary;
  previous_summary: PeriodSummary;
  by_category: CategoryTotal[];
  trend: TrendPoint[];
  recurring: RecurringSeries[];
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: unknown; correlation_id: string };
}
