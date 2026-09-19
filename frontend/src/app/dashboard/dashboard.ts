import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { MetricsService, Dashboard } from '../services/metrics';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss']
})
export class DashboardComponent implements OnInit {
  dashboard: Dashboard | null = null;

  // Trend Chart
  public trendChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    scales: { x: {}, y: { min: 0 } },
    plugins: {
      legend: { display: true },
    }
  };
  public trendChartType: ChartType = 'line';
  public trendChartData: ChartData<'line'> = {
    labels: [],
    datasets: []
  };

  // Category Donut Chart
  public donutChartOptions: ChartConfiguration['options'] = {
    responsive: true,
  };
  public donutChartType: ChartType = 'doughnut';
  public donutChartData: ChartData<'doughnut'> = {
    labels: [],
    datasets: []
  };

  constructor(private metricsService: MetricsService) {}

  ngOnInit() {
    this.metricsService.getDashboard().subscribe({
      next: (data) => {
        this.dashboard = data;
        this.updateCharts(data);
      },
      error: (err) => console.error('Failed to load dashboard', err)
    });
  }

  updateCharts(data: Dashboard) {
    // Trend Chart
    const labels = data.trend.map(t => t.period);
    const incomeData = data.trend.map(t => parseFloat(t.income));
    const expenseData = data.trend.map(t => parseFloat(t.expenses));

    this.trendChartData = {
      labels,
      datasets: [
        { data: incomeData, label: 'Income', borderColor: 'green', backgroundColor: 'rgba(0,128,0,0.1)', fill: true },
        { data: expenseData, label: 'Expenses', borderColor: 'red', backgroundColor: 'rgba(255,0,0,0.1)', fill: true }
      ]
    };

    // Donut Chart
    const donutLabels = data.by_category.map(c => c.category_name);
    const donutData = data.by_category.map(c => parseFloat(c.total));
    this.donutChartData = {
      labels: donutLabels,
      datasets: [{ data: donutData }]
    };
  }
}
