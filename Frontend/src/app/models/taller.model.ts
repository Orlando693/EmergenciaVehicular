export interface Taller {
  id_taller: number;
  id_usuario: number;
  razon_social: string;
  nombre_comercial: string;
  nit: string | null;
  telefono_atencion: string | null;
  email_atencion: string | null;
  direccion: string;
  referencia: string | null;
  latitud: number | null;
  longitud: number | null;
  capacidad_maxima: number;
  acepta_remolque: boolean;
  estado_registro: 'PENDIENTE' | 'APROBADO' | 'SUSPENDIDO' | 'RECHAZADO';
  calificacion_promedio: number | null;
  created_at: string;
  updated_at: string;
}

export interface TallerCreate {
  razon_social: string;
  nombre_comercial: string;
  nit?: string;
  telefono_atencion?: string;
  email_atencion?: string;
  direccion: string;
  referencia?: string;
  capacidad_maxima: number;
  acepta_remolque: boolean;
}
