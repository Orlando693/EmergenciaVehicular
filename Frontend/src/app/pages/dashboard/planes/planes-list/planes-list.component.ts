import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlanesService, PlanOut, SuscripcionOut } from '../../../../services/planes.service';
import { AuthService } from '../../../../core/services/auth.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-planes-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './planes-list.component.html',
  styleUrls: ['./planes-list.component.css'],
})
export class PlanesListComponent implements OnInit {
  planes: PlanOut[] = [];
  suscripcion: SuscripcionOut | null = null;
  loading = true;
  error = '';
  procesando: number | null = null;
  mensajeExito = '';

  constructor(
    private planesService: PlanesService,
    public auth: AuthService,
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.error = '';
    forkJoin({
      planes: this.planesService.listarPlanes(),
      suscripcion: this.planesService.miSuscripcion(),
    }).subscribe({
      next: ({ planes, suscripcion }) => {
        this.planes = planes;
        this.suscripcion = suscripcion;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudieron cargar los planes. Intenta nuevamente.';
        this.loading = false;
      },
    });
  }

  get esTaller(): boolean {
    return this.auth.rol === 'TALLER';
  }

  esPlanActual(plan: PlanOut): boolean {
    return this.suscripcion?.id_plan === plan.id_plan && this.suscripcion?.estado === 'ACTIVO';
  }

  suscribirse(plan: PlanOut): void {
    if (this.procesando || this.esPlanActual(plan)) return;
    this.procesando = plan.id_plan;
    this.mensajeExito = '';
    this.error = '';

    this.planesService.suscribir(plan.id_plan).subscribe({
      next: (sus) => {
        this.suscripcion = sus;
        this.procesando = null;
        this.mensajeExito = `¡Te has suscrito al plan ${plan.nombre} exitosamente!`;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'Error al procesar la suscripción.';
        this.procesando = null;
      },
    });
  }

  limiteTxt(valor: number, unidad: string): string {
    return valor === 0 ? `Ilimitado${unidad ? ' ' + unidad : ''}` : `${valor} ${unidad}`;
  }

  badgePlan(slug: string): string {
    if (slug === 'pro') return 'bg-amber-400 text-amber-900';
    if (slug === 'basico') return 'bg-blue-500 text-white';
    return 'bg-slate-200 text-slate-600';
  }
}
