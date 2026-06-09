import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { PlatformService, ReportePredictivo } from '../../../../services/platform.service';

@Component({
  selector: 'app-reportes-predictivos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reportes-predictivos.component.html',
  styleUrls: ['./reportes-predictivos.component.css'],
})
export class ReportesPredictivosComponent implements OnInit {
  reporte = signal<ReportePredictivo | null>(null);
  loading = signal(true);
  error = signal('');

  constructor(private platform: PlatformService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set('');
    this.platform.getReportePredictivo().subscribe({
      next: reporte => {
        this.reporte.set(reporte);
        this.loading.set(false);
      },
      error: error => {
        this.error.set(typeof error?.error?.detail === 'string' ? error.error.detail : 'No se pudo generar el reporte predictivo.');
        this.loading.set(false);
      },
    });
  }

  maxHistorico(): number {
    return Math.max(...(this.reporte()?.historico_global.map(item => item.incidentes) ?? [1]), 1);
  }

  barHeight(value: number): number {
    return Math.max(8, Math.round(value * 100 / this.maxHistorico()));
  }
}
