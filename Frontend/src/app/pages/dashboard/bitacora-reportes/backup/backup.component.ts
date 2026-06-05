import { Component, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { BackupService, BackupRegistro, BackupConfig, BackupConfigUpdate } from '../../../../services/backup.service';
import { AuthService } from '../../../../core/services/auth.service';
import { environment } from '../../../../../environments/environment';

@Component({
  selector: 'app-backup',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePipe],
  templateUrl: './backup.component.html',
  styleUrls: ['./backup.component.css'],
  encapsulation: ViewEncapsulation.None,
})
export class BackupComponent implements OnInit {
  private readonly token = () => this.auth.getToken() ?? '';

  backups       = signal<BackupRegistro[]>([]);
  config        = signal<BackupConfig | null>(null);
  loadingList   = signal(true);
  loadingManual = signal(false);
  loadingConfig = signal(false);
  loadingAuto   = signal(false);
  successMsg    = signal('');
  errorMsg      = signal('');

  // config form model
  cfgForm: BackupConfigUpdate = { activo: false, frecuencia: 'DIARIO', hora: '02:00' };

  constructor(
    private svc:  BackupService,
    private auth: AuthService,
    private http: HttpClient,
  ) {}

  ngOnInit() {
    this.cargarLista();
    this.cargarConfig();
    this.checkAuto();
  }

  /* ── lista ──────────────────────────────────────────────── */
  cargarLista() {
    this.loadingList.set(true);
    this.svc.listar().subscribe({
      next:  b  => { this.backups.set(b);  this.loadingList.set(false); },
      error: () => { this.errorMsg.set('Error al cargar backups.'); this.loadingList.set(false); },
    });
  }

  /* ── manual ─────────────────────────────────────────────── */
  generarManual() {
    this.loadingManual.set(true);
    this.errorMsg.set('');
    this.svc.generarManual().subscribe({
      next: b => {
        this.backups.update(list => [b, ...list]);
        this.loadingManual.set(false);
        this.flash(`Backup manual generado: ${b.nombre_archivo}`);
      },
      error: () => { this.errorMsg.set('Error al generar el backup.'); this.loadingManual.set(false); },
    });
  }

  /* ── descarga ───────────────────────────────────────────── */
  descargar(b: BackupRegistro) {
    const url = `${environment.apiUrl}/backup/${b.id_backup}/descargar`;
    const tok = this.token();
    this.http.get(url, {
      headers: { Authorization: `Bearer ${tok}` },
      responseType: 'blob',
    }).subscribe({
      next: blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = b.nombre_archivo ?? `backup_${b.id_backup}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
      },
      error: () => this.errorMsg.set('Error al descargar el backup.'),
    });
  }

  /* ── eliminar ───────────────────────────────────────────── */
  eliminar(b: BackupRegistro) {
    if (!confirm(`¿Eliminar backup ${b.nombre_archivo}? Esta acción no se puede deshacer.`)) return;
    this.svc.eliminar(b.id_backup).subscribe({
      next: () => {
        this.backups.update(list => list.filter(x => x.id_backup !== b.id_backup));
        this.flash('Backup eliminado.');
      },
      error: () => this.errorMsg.set('Error al eliminar el backup.'),
    });
  }

  /* ── config automático ──────────────────────────────────── */
  cargarConfig() {
    this.svc.obtenerConfig().subscribe({
      next: c => {
        this.config.set(c);
        this.cfgForm = { activo: c.activo, frecuencia: c.frecuencia, hora: c.hora };
      },
    });
  }

  guardarConfig() {
    this.loadingConfig.set(true);
    this.svc.actualizarConfig(this.cfgForm).subscribe({
      next: c => {
        this.config.set(c);
        this.cfgForm = { activo: c.activo, frecuencia: c.frecuencia, hora: c.hora };
        this.loadingConfig.set(false);
        this.flash('Configuración guardada.');
      },
      error: () => { this.errorMsg.set('Error al guardar configuración.'); this.loadingConfig.set(false); },
    });
  }

  /* ── check auto (al cargar página) ─────────────────────── */
  checkAuto() {
    this.svc.checkAuto().subscribe({
      next: r => { if (r.ejecutado) { this.cargarLista(); this.flash(`Backup automático ejecutado: ${r.nombre}`); } },
    });
  }

  /* ── helpers ────────────────────────────────────────────── */
  flash(msg: string) {
    this.successMsg.set(msg);
    setTimeout(() => this.successMsg.set(''), 4000);
  }

  formatBytes(b: number): string {
    if (b < 1024)        return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / 1024 / 1024).toFixed(2)} MB`;
  }
}
