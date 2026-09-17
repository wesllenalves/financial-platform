import { Component, inject, signal } from '@angular/core';

import { ApiService } from '../core/api.service';
import { formatMoney, formatPercent } from '../core/format';
import { Dashboard } from '../core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <div class="container grid">
      @if (data(); as d) {
        <section class="grid cols-4">
          <div class="panel">
            <p class="muted">Saldo atual</p>
            <p class="value">{{ money(d.current_balance) }}</p>
          </div>
          <div class="panel">
            <p class="muted">Receitas do mês</p>
            <p class="value positive">{{ money(d.summary.income) }}</p>
          </div>
          <div class="panel">
            <p class="muted">Despesas do mês</p>
            <p class="value negative">{{ money(d.summary.expenses) }}</p>
          </div>
          <div class="panel">
            <p class="muted">Taxa de poupança</p>
            <p class="value">{{ percent(d.summary.savings_rate) }}</p>
            <p class="muted">
              {{ d.summary.partial ? 'Mês em andamento — valores parciais' : 'Mês fechado' }}
            </p>
          </div>
        </section>

        <section class="grid cols-2">
          <div class="panel">
            <h2>Gastos por categoria</h2>
            @if (d.by_category.length === 0) {
              <p class="muted">Sem despesas neste mês.</p>
            }
            @for (item of d.by_category; track item.category_id) {
              <div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between">
                  <span>{{ item.category_name }}</span>
                  <span>{{ money(item.total) }} · {{ percent(item.share) }}</span>
                </div>
                <div class="bar"><span [style.width.%]="+item.share * 100"></span></div>
              </div>
            }
          </div>

          <div class="panel">
            <h2>Evolução mensal</h2>
            <table>
              <thead>
                <tr>
                  <th>Mês</th>
                  <th class="num">Receitas</th>
                  <th class="num">Despesas</th>
                </tr>
              </thead>
              <tbody>
                @for (point of d.trend; track point.period) {
                  <tr>
                    <td>{{ point.period }}</td>
                    <td class="num positive">{{ money(point.income) }}</td>
                    <td class="num negative">{{ money(point.expenses) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </section>

        <section class="panel">
          <h2>Gastos recorrentes detectados</h2>
          <p class="muted">
            Detecção determinística: mesmo estabelecimento, valor estável e intervalo mensal.
          </p>
          @if (d.recurring.length === 0) {
            <p class="muted">Nenhuma recorrência confirmada ainda.</p>
          } @else {
            <table>
              <thead>
                <tr>
                  <th>Descrição</th>
                  <th class="num">Ocorrências</th>
                  <th class="num">Valor médio</th>
                  <th>Último lançamento</th>
                  <th>Situação</th>
                </tr>
              </thead>
              <tbody>
                @for (series of d.recurring; track series.merchant_key) {
                  <tr>
                    <td>{{ series.description }}</td>
                    <td class="num">{{ series.occurrences }}</td>
                    <td class="num">{{ money(series.mean_amount) }}</td>
                    <td>{{ series.last_date }}</td>
                    <td>{{ series.active ? 'Ativo' : 'Parado' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </section>
      } @else {
        <p class="muted">Carregando…</p>
      }
    </div>
  `,
})
export class DashboardComponent {
  private readonly api = inject(ApiService);
  readonly data = signal<Dashboard | null>(null);

  readonly money = formatMoney;
  readonly percent = formatPercent;

  constructor() {
    this.api.dashboard().subscribe((dashboard) => this.data.set(dashboard));
  }
}
