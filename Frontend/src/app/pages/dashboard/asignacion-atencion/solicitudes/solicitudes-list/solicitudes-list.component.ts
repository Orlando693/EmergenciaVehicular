import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TallerService } from '../../../../../core/services/taller.service';
import { IncidenteOut } from '../../../../../core/services/incidente.service';

@Component({
  selector: 'app-solicitudes-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './solicitudes-list.component.html',
  styleUrl: './solicitudes-list.component.css',
})
export class SolicitudesListComponent implements OnInit {
  private tallerService = inject(TallerService);
  private router = inject(Router);

  solicitudes = signal<IncidenteOut[]>([]);
  cargando    = signal<boolean>(false);
  error       = signal<string | null>(null);

  ngOnInit(): void {
    this.cargarSolicitudes();
  }

  cargarSolicitudes() {
    this.cargando.set(true);
    this.error.set(null);
    this.tallerService.solicitudesDisponibles().subscribe({
      next: (data) => { this.solicitudes.set(data); this.cargando.set(false); },
      error: () => {
        this.error.set('No se pudieron cargar las solicitudes. Intenta nuevamente.');
        this.cargando.set(false);
      }
    });
  }

  verDetalle(id: number) {
    this.router.navigate(['/dashboard/solicitudes-disponibles/detalle', id]);
  }

  contar(clas: string): number {
    return this.solicitudes().filter(s => (s.clasificacion_ia || '').toUpperCase() === clas).length;
  }

  contarOtros(): number {
    const conocidas = ['COLISION', 'MECANICO'];
    return this.solicitudes().filter(s => !conocidas.includes((s.clasificacion_ia || '').toUpperCase())).length;
  }

  badgeClasificacion(clas?: string | null): string {
    const map: Record<string, string> = {
      COLISION:    'bg-red-100 text-red-700',
      MECANICO:    'bg-amber-100 text-amber-700',
      NEUMATICOS:  'bg-emerald-100 text-emerald-700',
      ELECTRICO:   'bg-violet-100 text-violet-700',
    };
    return map[(clas || '').toUpperCase()] ?? 'bg-slate-100 text-slate-600';
  }
}
