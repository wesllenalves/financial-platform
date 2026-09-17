export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—';
  }
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

export function formatPercent(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return '—';
  }
  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function apiErrorMessage(error: unknown): string {
  const body = (error as { error?: { error?: { message?: string } } })?.error?.error;
  return body?.message ?? 'Não foi possível concluir a operação.';
}
