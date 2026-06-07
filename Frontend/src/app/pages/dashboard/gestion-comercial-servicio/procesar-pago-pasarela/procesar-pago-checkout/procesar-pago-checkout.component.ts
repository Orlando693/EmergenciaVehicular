import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import {
  ProcesarPagoPasarelaService,
  InfoPagoOut,
  ProcesarPagoRequest,
  ResultadoPagoOut,
  PagoGatewayTransaccionOut
} from '../../../../../services/procesar-pago-pasarela.service';

type PantallaActiva = 'info' | 'formulario' | 'resultado' | 'historial';

@Component({
  selector: 'app-procesar-pago-checkout',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './procesar-pago-checkout.component.html',
  styleUrls: ['./procesar-pago-checkout.component.css']
})
export class ProcesarPagoCheckoutComponent implements OnInit {
  idIncidente!: number;
  pantalla: PantallaActiva = 'info';

  /* Datos de info */
  info: InfoPagoOut | null = null;
  loadingInfo = true;
  errorInfo = '';

  /* Formulario de pago */
  metodo: 'TARJETA' | 'TRANSFERENCIA' | 'QR' | 'EFECTIVO' = 'TARJETA';
  numeroTarjeta = '';
  nombreTitular = '';
  vencimiento = '';
  cvv = '';

  procesando = false;
  errorPago = '';

  /* Resultado */
  resultado: ResultadoPagoOut | null = null;

  /* Historial */
  transacciones: PagoGatewayTransaccionOut[] = [];
  loadingHistorial = false;

  constructor(
    private route: ActivatedRoute,
    private pagoService: ProcesarPagoPasarelaService
  ) {}

  ngOnInit(): void {
    this.idIncidente = Number(this.route.snapshot.paramMap.get('id'));
    this.cargarInfo();
  }

  cargarInfo(): void {
    this.loadingInfo = true;
    this.errorInfo = '';
    this.pagoService.obtenerInfo(this.idIncidente).subscribe({
      next: data => {
        this.info = data;
        this.loadingInfo = false;
        /* Si el servicio ya está pagado vamos directo al resultado simbólico */
        if (data.pago_estado === 'PAGADO') this.pantalla = 'resultado';
      },
      error: () => {
        this.errorInfo = 'No se pudo cargar la información del pago.';
        this.loadingInfo = false;
      }
    });
  }

  irAFormulario(): void {
    this.errorPago = '';
    this.pantalla = 'formulario';
  }

  get camposValidos(): boolean {
    if (this.metodo === 'TARJETA') {
      return this.numeroTarjeta.trim().length >= 4
        && this.nombreTitular.trim().length > 2
        && this.vencimiento.trim().length === 5
        && this.cvv.trim().length >= 3;
    }
    return true;
  }

  get qrReferencia(): string {
    const monto = Number(this.info?.monto_total ?? 0).toFixed(2).replace('.', '');
    return `EV-${this.idIncidente}-${monto}`;
  }

  get qrCells(): boolean[] {
    const payload = `EMERGENCIA_VEHICULAR|INC:${this.idIncidente}|MONTO:${Number(this.info?.monto_total ?? 0).toFixed(2)}|REF:${this.qrReferencia}`;
    return this.buildQrCells(payload);
  }

  confirmarPago(): void {
    if (!this.camposValidos || this.procesando) return;

    this.procesando = true;
    this.errorPago = '';

    const payload: ProcesarPagoRequest = {
      metodo_pago: this.metodo,
      ...(this.metodo === 'TARJETA' ? {
        numero_tarjeta: this.numeroTarjeta.replace(/\s/g, ''),
        nombre_titular: this.nombreTitular,
        vencimiento: this.vencimiento,
        cvv: this.cvv
      } : {})
    };

    this.pagoService.procesarPago(this.idIncidente, payload).subscribe({
      next: res => {
        this.resultado = res;
        this.procesando = false;
        this.pantalla = 'resultado';
        /* Refrescar info para que el badge actualice */
        this.cargarInfo();
      },
      error: err => {
        this.errorPago = err?.error?.detail ?? 'Error al procesar el pago. Verifica los datos e intenta de nuevo.';
        this.procesando = false;
      }
    });
  }

  verHistorial(): void {
    this.pantalla = 'historial';
    this.loadingHistorial = true;
    this.pagoService.listarTransacciones(this.idIncidente).subscribe({
      next: data => { this.transacciones = data; this.loadingHistorial = false; },
      error: () => this.loadingHistorial = false
    });
  }

  formatearTarjeta(event: Event): void {
    const input = event.target as HTMLInputElement;
    let val = input.value.replace(/\D/g, '').substring(0, 16);
    val = val.replace(/(.{4})/g, '$1 ').trim();
    this.numeroTarjeta = val;
  }

  formatearVencimiento(event: Event): void {
    const input = event.target as HTMLInputElement;
    let val = input.value.replace(/\D/g, '').substring(0, 4);
    if (val.length >= 3) val = val.slice(0, 2) + '/' + val.slice(2);
    this.vencimiento = val;
  }

  badgeEstado(estado: string): string {
    const mapa: Record<string, string> = {
      APROBADO:  'bg-emerald-100 text-emerald-700',
      RECHAZADO: 'bg-rose-100 text-rose-700',
      PENDIENTE: 'bg-amber-100 text-amber-700',
    };
    return mapa[estado] ?? 'bg-slate-100 text-slate-500';
  }

  iconoResultado(estado: string): string {
    if (estado === 'APROBADO' || estado === 'PAGADO') return '✅';
    if (estado === 'RECHAZADO') return '❌';
    return '⏳';
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
