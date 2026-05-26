import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { PagoService, CostoEstimado, PagoOut } from '../../../../services/pago.service';

type Metodo = 'TARJETA_CREDITO' | 'TARJETA_DEBITO' | 'TRANSFERENCIA' | 'EFECTIVO';
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
}
