export interface Tecnico {
  id_tecnico: number;
  id_taller: number;
  nombres: string;
  apellidos: string;
  telefono: string | null;
  especialidad: string | null;
  latitud: number | null;
  longitud: number | null;
  estado: 'DISPONIBLE' | 'OCUPADO' | 'INACTIVO';
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface TecnicoCreate {
  nombres: string;
  apellidos: string;
  telefono?: string;
  especialidad?: string;
}
