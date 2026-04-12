import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { TallerService } from '../../../core/services/taller.service';
import { AuthService } from '../../../core/services/auth.service';
import { Taller, TallerCreate } from '../../../models/taller.model';

@Component({
  selector: 'app-talleres',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './talleres.component.html',
  styleUrl: './talleres.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class TalleresComponent implements OnInit {
  talleres = signal<Taller[]>([]);
  loading  = signal(true);
  showForm = signal(false);
  success  = signal('');
  error    = signal('');
  saving   = signal(false);

  tallerEditando = signal<Taller | null>(null);
  savingEdit     = signal(false);
  editForm: FormGroup;

  form: FormGroup;
  esAdmin: boolean;

  constructor(
    private srv: TallerService,
    private auth: AuthService,
    private fb: FormBuilder,
  ) {
    this.esAdmin = this.auth.rol === 'ADMINISTRADOR';
    this.form = this.fb.group({
      razon_social:     ['', Validators.required],
      nombre_comercial: ['', Validators.required],
      nit:              [''],
      telefono_atencion:[''],
      email_atencion:   [''],
      direccion:        ['', Validators.required],
      referencia:       [''],
      capacidad_maxima: [1, [Validators.required, Validators.min(1)]],
      acepta_remolque:  [false],
    });
    this.editForm = this.fb.group({
      razon_social:     ['', Validators.required],
      nombre_comercial: ['', Validators.required],
      nit:              [''],
      telefono_atencion:[''],
      email_atencion:   [''],
      direccion:        ['', Validators.required],
      referencia:       [''],
      capacidad_maxima: [1, [Validators.required, Validators.min(1)]],
      acepta_remolque:  [false],
    });
  }

  ngOnInit() { this.cargar(); }

  cargar() {
    this.loading.set(true);
    this.srv.listar().subscribe({
      next: (d) => { this.talleres.set(d); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar talleres'); this.loading.set(false); },
    });
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const data: TallerCreate = this.form.value;
    this.srv.registrar(data).subscribe({
      next: () => {
        this.success.set('Taller registrado. Pendiente de aprobación.');
        this.showForm.set(false); this.form.reset({ capacidad_maxima: 1, acepta_remolque: false });
        this.cargar(); this.saving.set(false);
        setTimeout(() => this.success.set(''), 4000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error'); this.saving.set(false); },
    });
  }

  abrirEdicion(t: Taller) {
    this.tallerEditando.set(t);
    this.editForm.patchValue({
      razon_social:     t.razon_social,
      nombre_comercial: t.nombre_comercial,
      nit:              t.nit ?? '',
      telefono_atencion:t.telefono_atencion ?? '',
      email_atencion:   t.email_atencion ?? '',
      direccion:        t.direccion,
      referencia:       t.referencia ?? '',
      capacidad_maxima: t.capacidad_maxima,
      acepta_remolque:  t.acepta_remolque,
    });
    this.error.set('');
    this.showForm.set(false);
  }

  cerrarEdicion() {
    this.tallerEditando.set(null);
    this.error.set('');
  }

  guardarEdicion() {
    if (this.editForm.invalid) { this.editForm.markAllAsTouched(); return; }
    const t = this.tallerEditando();
    if (!t) return;
    this.savingEdit.set(true);
    this.error.set('');
    const data = this.editForm.value;
    
    // Si es administrador, usa actualizarTallerAdmin, sino el de taller personal
    const req = this.esAdmin ? this.srv.actualizarTallerAdmin(t.id_taller, data) : this.srv.actualizar(data);
    
    req.subscribe({
      next: (updated) => {
        this.talleres.update(list => list.map(x => x.id_taller === t.id_taller ? updated : x));
        this.success.set('Taller actualizado correctamente');
        this.cerrarEdicion();
        this.savingEdit.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (err) => {
        this.error.set(err.error?.detail ?? 'Error al actualizar taller');
        this.savingEdit.set(false);
      },
    });
  }

  aprobar(taller: Taller) {
    this.srv.cambiarEstado(taller.id_taller, 'APROBADO').subscribe({
      next: () => this.cargar(),
      error: (e) => this.error.set(e.error?.detail ?? 'Error'),
    });
  }

  rechazar(taller: Taller) {
    this.srv.cambiarEstado(taller.id_taller, 'RECHAZADO').subscribe({
      next: () => this.cargar(),
      error: (e) => this.error.set(e.error?.detail ?? 'Error'),
    });
  }

  estadoBadge(estado: string): string {
    const map: Record<string, string> = {
      PENDIENTE: 'badge-yellow', APROBADO: 'badge-green',
      SUSPENDIDO: 'badge-red',  RECHAZADO: 'badge-red',
    };
    return map[estado] ?? 'badge-gray';
  }
}
