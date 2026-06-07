import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { PagoService, CostoEstimado, PagoOut } from '../../../../services/pago.service';

type Metodo = 'TARJETA_CREDITO' | 'TARJETA_DEBITO' | 'TRANSFERENCIA' | 'QR' | 'EFECTIVO';
type PasoView = 'COSTO' | 'PAGO' | 'RESULTADO';

@Component({
  selector: 'app-pago-checkout',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pago-checkout.component.html',
})
export class PagoCheckoutComponent implements OnInit {
  private route  = inject(ActivatedRoute);
  private router = inject(Router);
  private pagoSvc = inject(PagoService);

  idIncidente = signal(0);
  paso        = signal<PasoView>('COSTO');
  cargando    = signal(true);
  procesando  = signal(false);
  error       = signal<string | null>(null);

  costo       = signal<CostoEstimado | null>(null);
  resultado   = signal<PagoOut | null>(null);

  metodo      = signal<Metodo>('TARJETA_CREDITO');
  qrReferencia = computed(() => `EV-${this.idIncidente()}-${Number(this.costo()?.monto_total ?? 0).toFixed(2).replace('.', '')}`);
  qrPayload = computed(() => `EMERGENCIA_VEHICULAR|INC:${this.idIncidente()}|MONTO:${Number(this.costo()?.monto_total ?? 0).toFixed(2)}|REF:${this.qrReferencia()}`);
  qrCells = computed(() => this.buildQrCells(this.qrPayload()));

  // Campos de tarjeta (solo display / mock)
  numTarjeta  = '';
  titular     = '';
  vencimiento = '';
  cvv         = '';

  readonly metodos: { key: Metodo; label: string; icon: string }[] = [
    { key: 'TARJETA_CREDITO', label: 'Tarjeta de Crédito', icon: '💳' },
    { key: 'TARJETA_DEBITO',  label: 'Tarjeta de Débito',  icon: '💰' },
    { key: 'TRANSFERENCIA',   label: 'Transferencia',       icon: '🏦' },
    { key: 'EFECTIVO',        label: 'Efectivo',            icon: '💵' },
  ];

  ngOnInit() {
    this.idIncidente.set(Number(this.route.snapshot.paramMap.get('id')));
    this.pagoSvc.obtenerCosto(this.idIncidente()).subscribe({
      next: (c) => {
        this.costo.set(c);
        // Si ya tiene pago completado, ir directo a resultado
        if (c.pago_existente?.estado === 'COMPLETADO') {
          this.resultado.set(c.pago_existente);
          this.paso.set('RESULTADO');
        }
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'No se pudo cargar el costo del servicio.');
        this.cargando.set(false);
      },
    });
  }

  irAPago() { this.paso.set('PAGO'); }

  pagar() {
    const esTarjeta = this.metodo().startsWith('TARJETA');
    if (esTarjeta && this.numTarjeta.replace(/\s/g, '').length < 16) {
      this.error.set('Ingresa un número de tarjeta válido (16 dígitos).');
      return;
    }
    this.error.set(null);
    this.procesando.set(true);

    this.pagoSvc.realizarPago(this.idIncidente(), {
      metodo_pago:     this.metodo(),
      numero_tarjeta:  this.numTarjeta.replace(/\s/g, '') || undefined,
      nombre_titular:  this.titular  || undefined,
      vencimiento:     this.vencimiento || undefined,
      cvv:             this.cvv || undefined,
    }).subscribe({
      next: (pago) => {
        this.resultado.set(pago);
        this.paso.set('RESULTADO');
        this.procesando.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Error al procesar el pago. Intenta de nuevo.');
        this.procesando.set(false);
      },
    });
  }

  reintentar() {
    this.error.set(null);
    this.resultado.set(null);
    this.paso.set('PAGO');
  }

  volver() {
    this.router.navigate(['/dashboard/incidentes/detalle', this.idIncidente()]);
  }

  formatCard(value: string): string {
    return value.replace(/\D/g, '').substring(0, 16).replace(/(.{4})/g, '$1 ').trim();
  }

  onCardInput(event: Event) {
    const input = event.target as HTMLInputElement;
    this.numTarjeta = this.formatCard(input.value);
    input.value = this.numTarjeta;
  }

  private buildQrCells(payload: string): boolean[] {
    const size = 13;
    let seed = 0;
    for (let i = 0; i < payload.length; i++) {
      seed = (seed * 31 + payload.charCodeAt(i)) >>> 0;
    }
    const cells: boolean[] = [];
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const inFinder =
          (x < 4 && y < 4) ||
          (x >= size - 4 && y < 4) ||
          (x < 4 && y >= size - 4);
        if (inFinder) {
          const localX = x < 4 ? x : x - (size - 4);
          const localY = y < 4 ? y : y - (size - 4);
          cells.push(localX === 0 || localX === 3 || localY === 0 || localY === 3 || (localX === 1 && localY === 1));
          continue;
        }
        const bit = ((seed >> ((x + y * 3) % 24)) ^ (x * 17) ^ (y * 29) ^ seed) & 1;
        cells.push(bit === 1);
      }
    }
    return cells;
  }
}
