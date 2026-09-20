import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FindingService, Finding } from '../../services/finding';

@Component({
  selector: 'app-findings-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './findings-list.html',
  styleUrls: ['./findings-list.scss']
})
export class FindingsList implements OnInit {
  findings: Finding[] = [];
  selectedPeriod: string = new Date().toISOString().substring(0, 7); // YYYY-MM
  isLoading = false;
  runMessage = '';

  expandedFindingId: string | null = null;

  constructor(private findingService: FindingService) {}

  ngOnInit() {
    this.loadFindings();
  }

  loadFindings() {
    this.isLoading = true;
    this.findingService.listFindings().subscribe({
      next: (data) => {
        this.findings = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching findings', err);
        this.isLoading = false;
      }
    });
  }

  runAnalysis() {
    this.isLoading = true;
    this.runMessage = '';

    this.findingService.runAnalysis(this.selectedPeriod).subscribe({
      next: (res) => {
        this.runMessage = `Analysis complete. Found ${res.findings_count} findings.`;
        this.loadFindings();
      },
      error: (err) => {
        console.error('Analysis failed', err);
        this.runMessage = 'Analysis failed. Please try again.';
        this.isLoading = false;
      }
    });
  }

  toggleEvidence(id: string) {
    if (this.expandedFindingId === id) {
      this.expandedFindingId = null;
    } else {
      this.expandedFindingId = id;
    }
  }

  formatEvidence(evidence: any): string {
    return JSON.stringify(evidence, null, 2);
  }
}
