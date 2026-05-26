import {
  Component, inject, OnInit, OnDestroy, signal, ElementRef, ViewChild, AfterViewChecked
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ChatService, MensajeChat, MensajeWS } from '../../../../services/chat.service';
import { AuthService } from '../../../../core/services/auth.service';
import { IncidenteService, IncidenteOut } from '../../../../core/services/incidente.service';

interface MensajeUI {
  tipo:          'mensaje' | 'sistema';
  id_usuario?:   number;
  nombre_emisor: string;
  rol_emisor:    string;
  contenido:     string;
  created_at:    string;
  propio:        boolean;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './chat.component.html',
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesEnd') private messagesEnd!: ElementRef;

  private route      = inject(ActivatedRoute);
  private router     = inject(Router);
  private chatSvc    = inject(ChatService);
  public  auth       = inject(AuthService);
  private incSvc     = inject(IncidenteService);

  idIncidente   = signal<number>(0);
  incidente     = signal<IncidenteOut | null>(null);
  mensajes      = signal<MensajeUI[]>([]);
  texto         = '';
  cargando      = signal(true);
  wsConectado   = signal(false);
  enLinea       = signal(0);

  private shouldScroll = false;

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.idIncidente.set(id);

    // Cargar datos del incidente
    this.incSvc.obtenerDetalle(id).subscribe({
      next: inc => this.incidente.set(inc),
      error: () => {},
    });

    // Cargar historial
    this.chatSvc.obtenerHistorial(id).subscribe({
      next: (data) => {
        this.enLinea.set(data.en_linea);
        const hist: MensajeUI[] = data.mensajes.map(m => this.toUI(m));
        this.mensajes.set(hist);
        this.cargando.set(false);
        this.shouldScroll = true;
        this.conectarWS();
      },
      error: () => {
        this.cargando.set(false);
        this.conectarWS();
      },
    });
  }

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollBottom();
      this.shouldScroll = false;
    }
  }

  ngOnDestroy() { this.chatSvc.desconectar(); }

  private conectarWS() {
    const token = this.auth.getToken();
    if (!token) return;

    this.chatSvc.conectar(
      this.idIncidente(),
      token,
      (msg: MensajeWS) => this.onMensaje(msg),
      () => this.wsConectado.set(true),
      () => this.wsConectado.set(false),
    );
  }

  private onMensaje(msg: MensajeWS) {
    if (msg.tipo === 'sistema') {
      this.mensajes.update(list => [...list, {
        tipo: 'sistema', nombre_emisor: '', rol_emisor: '', contenido: msg.contenido,
        created_at: msg.created_at, propio: false,
      }]);
    } else {
      this.mensajes.update(list => [...list, {
        tipo: 'mensaje',
        id_usuario:    msg.id_usuario,
        nombre_emisor: msg.nombre_emisor ?? '',
        rol_emisor:    msg.rol_emisor ?? '',
        contenido:     msg.contenido,
        created_at:    msg.created_at,
        propio:        msg.id_usuario === this.auth.idUsuario,
      }]);
    }
    this.shouldScroll = true;
  }

  enviar() {
    const txt = this.texto.trim();
    if (!txt || !this.wsConectado()) return;
    this.chatSvc.enviar(txt);
    this.texto = '';
  }

  onEnter(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.enviar();
    }
  }

  private scrollBottom() {
    try {
      this.messagesEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' });
    } catch { /* no-op */ }
  }

  private toUI(m: MensajeChat): MensajeUI {
    return {
      tipo:          'mensaje',
      id_usuario:    m.id_usuario,
      nombre_emisor: m.nombre_emisor,
      rol_emisor:    m.rol_emisor,
      contenido:     m.contenido,
      created_at:    m.created_at,
      propio:        m.id_usuario === this.auth.idUsuario,
    };
  }

  colorRol(rol: string): string {
    const map: Record<string, string> = {
      CLIENTE:       'bg-blue-100 text-blue-700',
      TALLER:        'bg-orange-100 text-orange-700',
      ADMINISTRADOR: 'bg-violet-100 text-violet-700',
    };
    return map[rol] ?? 'bg-slate-100 text-slate-600';
  }

  volver() { this.router.navigate(['/dashboard/incidentes/detalle', this.idIncidente()]); }
}
