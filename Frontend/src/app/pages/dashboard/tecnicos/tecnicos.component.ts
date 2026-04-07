import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { TecnicoService } from '../../../core/services/tecnico.service';
import { TallerService } from '../../../core/services/taller.service';
import { AuthService } from '../../../core/services/auth.service';
import { Tecnico, TecnicoCreate } from '../../../models/tecnico.model';

@Component({
  selector: 'app-tecnicos',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tecnicos.component.html',
  styleUrl: './tecnicos.component.css',
  encapsulation: ViewEncapsulation.None,
})
export class TecnicosComponent implements OnInit {
  tecnicos  = signal<Tecnico[]>([]);
  loading   = signal(true);
  showForm  = signal(false);
  success   = signal('');
  error     = signal('');
  saving    = signal(false);
  idTaller  = signal(0);

  form: FormGroup;

  constructor(
    private srv: TecnicoService,
    private tallerSrv: TallerService,
    private auth: AuthService,
    private fb: FormBuilder,
  ) {
    this.form = this.fb.group({
      nombres:     ['', Validators.required],
      apellidos:   ['', Validators.required],
      telefono:    [''],
      especialidad:[''],
    });
  }

  ngOnInit() {
    this.tallerSrv.miTaller().subscribe({
      next: (t) => { this.idTaller.set(t.id_taller); this.cargar(); },
      error: () => { this.error.set('No tienes un taller registrado'); this.loading.set(false); },
    });
  }

  cargar() {
    if (!this.idTaller()) return;
    this.loading.set(true);
    this.srv.listar(this.idTaller()).subscribe({
      next: (d) => { this.tecnicos.set(d); this.loading.set(false); },
      error: () => { this.error.set('Error al cargar técnicos'); this.loading.set(false); },
    });
  }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const data: TecnicoCreate = this.form.value;
    this.srv.crear(this.idTaller(), data).subscribe({
      next: () => {
        this.success.set('Técnico registrado correctamente');
        this.showForm.set(false); this.form.reset();
        this.cargar(); this.saving.set(false);
        setTimeout(() => this.success.set(''), 3000);
      },
      error: (e) => { this.error.set(e.error?.detail ?? 'Error'); this.saving.set(false); },
    });
  }

  desactivar(t: Tecnico) {
    this.srv.desactivar(this.idTaller(), t.id_tecnico).subscribe({
      next: () => this.cargar(),
      error: (e) => this.error.set(e.error?.detail ?? 'Error'),
    });
  }

  estadoBadge(estado: string): string {
    const map: Record<string, string> = { DISPONIBLE: 'badge-green', OCUPADO: 'badge-yellow', INACTIVO: 'badge-gray' };
    return map[estado] ?? 'badge-gray';
  }
}
