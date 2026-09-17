import { apiErrorMessage, formatMoney, formatPercent } from './format';

describe('formatting helpers', () => {
  it('formats money in Brazilian reais', () => {
    expect(formatMoney('1234.56').replace(/\u00a0/g, ' ')).toBe('R$ 1.234,56');
  });

  it('shows a dash instead of inventing a value', () => {
    expect(formatMoney(null)).toBe('—');
    expect(formatPercent(null)).toBe('—');
  });

  it('formats a savings rate as a percentage', () => {
    expect(formatPercent('0.3894')).toBe('38.9%');
  });

  it('surfaces the API error message when present', () => {
    const error = { error: { error: { message: 'E-mail já cadastrado.' } } };
    expect(apiErrorMessage(error)).toBe('E-mail já cadastrado.');
    expect(apiErrorMessage(new Error('boom'))).toBe('Não foi possível concluir a operação.');
  });
});
